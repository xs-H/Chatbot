import threading

from asr.models.TranscribeTask import TranscribeTask
from asr.services.transcribe.WhisperTranscriber import WhisperTranscriber

task_store = {}

whisper_transcriber = WhisperTranscriber()


class TaskManager:
    def __init__(self, task: TranscribeTask):
        self.task = task
        self.store("__processing")

        threading.Thread(target=whisper_transcribe, args=(self,)).start()

    def store(self, result):
        task_store[self.task.task_id] = result

    @staticmethod
    def get_task_status(task_id):
        content = task_store.get(task_id, "__not_found")
        if content == "__processing":
            return "processing"
        elif content == "__not_found":
            return "not_found"
        elif content.startswith("__error:"):
            return "error"
        else:
            return "done"

    @staticmethod
    def get_task_result(task_id):
        status = TaskManager.get_task_status(task_id)
        if status == "done":
            return task_store[task_id]
        elif status == "error":
            return task_store[task_id].split("__error:")[1]
        else:
            return None


def whisper_transcribe(mgr: TaskManager):
    # Placeholder for the actual transcription logic
    # This should call the Whisper model or any other ASR model
    try:
        text = whisper_transcriber.transcribe(audio_path=mgr.task.file_path)
        mgr.store(text)
    except Exception as e:
        mgr.store(f"__error: {str(e)}")
    finally:
        return


__all__ = [
    "TaskManager",
    "task_store",
]
