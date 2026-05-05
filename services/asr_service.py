"""
ASR 服务（本地 Whisper）
- 使用已安装的 openai-whisper，无需 Docker
- 支持上传音频文件并返回识别文本
- 模型在首次使用时懒加载（避免占用未使用时的显存）
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import whisper

from config import ASRConfig, PathConfig
from utils.logger import get_logger

logger = get_logger("services.asr", "asr.log")


class ASRService:
    """
    ASR 服务（单例，由 main.py lifespan 初始化）
    Whisper 模型懒加载：第一次 transcribe 调用时加载。
    """

    def __init__(self) -> None:
        self._model_size = ASRConfig.MODEL_SIZE
        self._language   = ASRConfig.LANGUAGE
        self._model: whisper.Whisper | None = None
        logger.info(
            f"ASR 服务已初始化（模型：{self._model_size}，语言：{self._language}）"
            "，Whisper 模型将在首次请求时加载。"
        )

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        logger.info(f"首次加载 Whisper 模型 [{self._model_size}]…")
        download_root = str(PathConfig.WHISPER_CACHE_DIR) if PathConfig.WHISPER_CACHE_DIR else None
        self._model = whisper.load_model(
            self._model_size,
            download_root=download_root,
        )
        logger.info("Whisper 模型加载完成。")

    # ── 对外接口 ─────────────────────────────────────────────────────────────

    def transcribe(self, audio_bytes: bytes, suffix: str = ".wav") -> str:
        """
        接收原始音频字节，返回识别文本。
        suffix：文件后缀，如 '.wav' / '.mp3' / '.m4a'
        """
        self._ensure_loaded()

        # 写入临时文件（Whisper 接收文件路径）
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            result = self._model.transcribe(  # type: ignore[union-attr]
                tmp_path,
                language=self._language,
                fp16=False,   # CPU 推理时关闭 fp16；GPU 可改为 True
            )
        except Exception as e:
            logger.error(f"Whisper 识别失败：{e}")
            raise RuntimeError(f"ASR 识别错误：{e}") from e
        finally:
            os.unlink(tmp_path)

        text: str = result.get("text", "").strip()
        logger.info(f"ASR 识别结果：{text[:80]}…" if len(text) > 80 else f"ASR 识别结果：{text}")
        return text
