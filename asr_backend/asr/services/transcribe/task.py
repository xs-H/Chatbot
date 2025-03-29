import threading

from asr.services.transcribe.task_store import task_store


class TranscribeService:
    def __init__(self, task_id, file_path):
        self.task_id = task_id
        self.file_path = file_path
        self.store("__processing")

        self.start_task()

    def store(self, result):
        # Set task result
        task_store[self.task_id] = result

    def start_task(self):
        threading.Thread(target=whisper_transcribe, args=(self,)).start()

    @staticmethod
    def get_task_status(task_id):
        # Get task status
        content = task_store.get(task_id, "__not_found")
        if content == "__processing":
            return "processing"
        elif content == "__not_found":
            return "not_found"
        elif content.startswith("__error:"):
            return "error"
        else:
            return "done"


def whisper_transcribe(t: TranscribeService):
    # Placeholder for the actual transcription logic
    # This should call the Whisper model or any other ASR model
    try:
        print(task_store)
        text = f"Transcribed {t.file_path}"
        t.store(text)
        print(task_store)
    except Exception as e:
        t.store(f"__error: {str(e)}")
    finally:
        return
