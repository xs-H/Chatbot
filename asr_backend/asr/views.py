import datetime
import os

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from rest_framework import status as code
from rest_framework.response import Response
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
        status=400,
    )


class TranscribeView(APIView):
    def post(self, request):
        file = request.FILES.get("file")

        if not file:
            return bad_request("Missing 'file'")

        task_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")

        save_dir = settings.SAVE_MEDIA_DIR
        save_dir = os.path.join(save_dir, task_id)

        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, file.name)

        with open(file_path, "wb") as f:
            for chunk in file.chunks():
                f.write(chunk)

        task = TranscribeTask(task_id=task_id, file_path=file_path)
        transcribe.TaskManager(task)

        return Response({"task_id": task_id}, status=code.HTTP_201_CREATED)

    def get(self, request, task_id):
        if not task_id:
            return bad_request("Missing 'task_id'")

        status = transcribe.TaskManager.get_task_status(task_id)

        res = {}
        res["status"] = status

        if status == "not_found":
            return Response({}, status=code.HTTP_404_NOT_FOUND)
        elif status == "processing":
            return Response({}, status=code.HTTP_202_ACCEPTED)
        elif status == "error":
            return Response(
                {
                    "task_id": task_id,
                    "status": status,
                    "text": transcribe.TaskManager.get_task_result(task_id),
                },
                status=code.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        else:
            return Response(
                {
                    "task_id": task_id,
                    "status": status,
                    "text": transcribe.TaskManager.get_task_result(task_id),
                },
                status=code.HTTP_200_OK,
            )
