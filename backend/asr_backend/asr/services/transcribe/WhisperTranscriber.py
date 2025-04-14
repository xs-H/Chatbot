import logging
import time
from typing import Any, Dict

import whisper
from django.conf import settings

logger = logging.getLogger(__name__)


class WhisperTranscriber:
    _instance = None

    def __init__(self, model_name: str = settings.WHISPER_MODEL):
        logger.info(f"Loading Whisper model: {model_name}")
        self.model_name = model_name
        self.model = whisper.load_model(model_name)

    @classmethod
    def get_instance(cls) -> "WhisperTranscriber":
        if cls._instance is None:
            cls._instance = cls(settings.WHISPER_MODEL)
        return cls._instance

    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        # 执行转写
        logger.debug(f"Transcribing audio file: {audio_path}")
        start_time = time.time()
        result: Dict[str, Any] = self.model.transcribe(audio_path)
        end_time = time.time()
        logger.debug(f"Transcription result: {result['text']}")
        logger.debug(f"Transcription time: {end_time - start_time:.2f} seconds")

        return result
