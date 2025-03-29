import json
import os
from typing import Any, Dict

import whisper
from django.conf import settings


class WhisperTranscriber:
    def __init__(self, model_name: str = settings.WHISPER_MODEL):
        self.model_name = model_name
        self.model = whisper.load_model(model_name)

    def transcribe(self, audio_path: str) -> str:
        # 执行转写
        result: Dict[str, Any] = self.model.transcribe(audio_path)
        text: str = result["text"]

        # 生成保存路径
        audio_dir = os.path.dirname(audio_path)
        json_path = os.path.join(audio_dir, "text.json")

        # 保存为 JSON 文件
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return text
