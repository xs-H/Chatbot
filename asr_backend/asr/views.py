import datetime
import logging
import os

from django.conf import settings
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
from asr.services import transcribe


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

        save_dir = settings.SAVE_MEDIA_DIR
        save_dir = os.path.join(save_dir, task_id)

        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, file.name)

        with open(file_path, "wb") as f:
            for chunk in file.chunks():
                f.write(chunk)

        TranscribeView.logger.debug(f"File saved to: {file_path}")

        task = TranscribeTask(task_id=task_id, file_path=file_path)
        transcribe.TaskManager(task)

        return Response({"task_id": task_id}, status=HTTP_201_CREATED)

    def get(self, request, task_id):
        if not task_id:
            return bad_request("Missing 'task_id'")

        TranscribeView.logger.debug(f"Received qurey task_id: {task_id}")

        task_status = transcribe.TaskManager.get_task_status(task_id)

        TranscribeView.logger.debug(f"Task status: {task_status}")

        if task_status == "not_found":
            return Response(status=HTTP_404_NOT_FOUND)
        elif task_status == "processing":
            return Response(status=HTTP_202_ACCEPTED)
        else:
            res = {}
            res["task_id"] = task_id
            res["status"] = task_status
            res["text"] = transcribe.TaskManager.get_task_result(task_id)

            res_code = (
                HTTP_200_OK
                if res["status"] == "done"
                else HTTP_500_INTERNAL_SERVER_ERROR
            )
            return Response(
                res,
                status=res_code,
            )
