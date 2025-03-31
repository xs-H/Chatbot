import datetime
import logging
import os

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from rest_framework.views import APIView

from asr.models.TranscribeTask import TranscribeTask
from asr.services.transcribe.TaskManager import TaskManager


@require_GET
def health_check(request):
    return JsonResponse(
        {
            "status": "ok",
            "service": "asr-backend",
            "version": "1.0",
        }
    )


def bad_request(msg: str):
    return JsonResponse(
        {
            "error": msg,
        },
        status=HTTP_400_BAD_REQUEST,
    )


class TranscribeView(APIView):
    logger = logging.getLogger(f"{__name__}.TranscribeView")

    def post(self, request):
        file = request.FILES.get("file")

        if not file:
            return bad_request("Missing 'file'")

        TranscribeView.logger.debug(f"Received file: {file.name}")

        task_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
        save_dir = TaskManager.get_task_dir(task_id)
        os.makedirs(save_dir, exist_ok=True)

        file_path = os.path.join(save_dir, file.name)

        with open(file_path, "wb") as f:
            for chunk in file.chunks():
                f.write(chunk)

        TranscribeView.logger.debug(f"File saved to: {file_path}")

        task = TranscribeTask(task_id=task_id, file_path=file_path)
        TaskManager(task)

        return Response({"task_id": task_id}, status=HTTP_201_CREATED)

    def get(self, request, task_id):
        if not task_id:
            return bad_request("Missing 'task_id'")

        TranscribeView.logger.debug(f"Received qurey task_id: {task_id}")

        status, result = TaskManager.get_task_result(task_id)

        TranscribeView.logger.debug(f"Task status: {status}")

        res = {"task_id": task_id, "status": status, "result": ""}

        if status == "not_found":
            return Response(res, status=HTTP_404_NOT_FOUND)
        elif status == "processing":
            return Response(res, status=HTTP_202_ACCEPTED)
        else:
            res["result"] = result
            res_code = (
                HTTP_200_OK if status == "done" else HTTP_500_INTERNAL_SERVER_ERROR
            )
            return Response(res, status=res_code)
