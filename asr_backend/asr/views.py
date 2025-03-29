import datetime
import os

from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from asr.services.transcribe import task


@require_GET
def health_check(request):
    return JsonResponse(
        {
            "status": "ok",
            "service": "asr-backend",
            "version": "1.0",
        }
    )


@method_decorator(csrf_exempt, name="dispatch")
class TranscribeView(View):
    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return JsonResponse({"error": "Missing 'file'"}, status=400)

        task_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")

        save_dir = settings.SAVE_DIR
        save_dir = os.path.join(save_dir, task_id)

        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, file.name)

        with open(file_path, "wb") as f:
            for chunk in file.chunks():
                f.write(chunk)

        task.TranscribeService(task_id, file_path)

        return JsonResponse({"task_id": task_id}, status=201)

    def get(self, request):
        return JsonResponse({"message": "GET request for transcription"})
