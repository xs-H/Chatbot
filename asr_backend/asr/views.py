import datetime
import os

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

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


@method_decorator(csrf_exempt, name="dispatch")
class TranscribeView(View):
    def post(self, request):
        file = request.FILES.get("file")

        if not file:
            return bad_request("Missing 'file'")

        task_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")

        save_dir = settings.SAVE_DIR
        save_dir = os.path.join(save_dir, task_id)

        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, file.name)

        with open(file_path, "wb") as f:
            for chunk in file.chunks():
                f.write(chunk)

        task = TranscribeTask(task_id=task_id, file_path=file_path)
        transcribe.TaskManager(task)

        return JsonResponse({"task_id": task_id}, status=201)

    def get(self, request, task_id):
        if not task_id:
            return bad_request("Missing 'task_id'")

        status = transcribe.TaskManager.get_task_status(task_id)

        res = {}
        res["task_id"] = task_id
        res["status"] = status
        res["text"] = transcribe.TaskManager.get_task_result(task_id)

        if status == "not_found":
            return HttpResponse(status=404)
        elif status == "processing":
            return HttpResponse(status=202)
        elif status == "error":
            return JsonResponse(res, status=500)
        else:
            return JsonResponse(res, status=200)
