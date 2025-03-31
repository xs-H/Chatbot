import json
import os
import threading
from pathlib import Path

from django.conf import settings

from asr.models.TranscribeTask import TranscribeTask
from asr.services.transcribe.WhisperTranscriber import WhisperTranscriber


class TaskManager:
    TASK_RESULT_FILE = "result.json"
    TASK_ERROR_FILE = "error.log"

    def __init__(self, task: TranscribeTask):
        self.task = task

        threading.Thread(target=whisper_transcribe, args=(self,)).start()

    @staticmethod
    def get_task_dir(task_id: str) -> Path:
        return Path(settings.SAVE_MEDIA_DIR) / task_id

    @staticmethod
    def get_task_result(task_id) -> tuple[str, dict]:
        task_dir = TaskManager.get_task_dir(task_id)
        if not os.path.exists(task_dir):
            return "not_found", {}

        error_log = task_dir / TaskManager.TASK_ERROR_FILE
        result_json = task_dir / TaskManager.TASK_RESULT_FILE

        if os.path.exists(error_log):
            with open(error_log, "r", encoding="utf-8") as f:
                return "error", {"error": f.read()}
        elif os.path.exists(result_json):
            with open(result_json, "r", encoding="utf-8") as f:
                # Get JSON result
                try:
                    json_data = json.load(f)
                except Exception as e:
                    json_data = {
                        "error": str(e),
                        "message": "Failed to parse result.json",
                    }
            return "done", json_data
        else:
            return "processing", {}

    def save_task_error(self, content: str):
        task_dir = TaskManager.get_task_dir(self.task.task_id)
        error_log = os.path.join(task_dir, TaskManager.TASK_ERROR_FILE)

        with open(error_log, "w", encoding="utf-8") as f:
            f.write(content)
        return

    def save_task_result(self, src: dict):
        task_dir = TaskManager.get_task_dir(self.task.task_id)
        result_json = os.path.join(task_dir, TaskManager.TASK_RESULT_FILE)

        with open(result_json, "w", encoding="utf-8") as f:
            json.dump(src, f, ensure_ascii=False, indent=2)


def whisper_transcribe(mgr: TaskManager):
    try:
        model = WhisperTranscriber.get_instance()
        result = model.transcribe(audio_path=mgr.task.file_path)
        mgr.save_task_result(result)
    except Exception as e:
        error_msg = str(e)
        TaskManager.save_task_error(mgr.task.task_id, error_msg)
        return
    finally:
        return
