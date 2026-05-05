"""
TTS 服务（CosyVoice2）
- 在模块加载前完成 sys.path 注入（必须最先执行）
- 使用线程锁保证 GPU 串行推理，避免显存溢出
- 对上层提供 synthesize(text) → 音频文件路径 接口
"""
from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path
from threading import Lock

import torch
import torchaudio
from snownlp import SnowNLP

from config import PathConfig, TTSConfig
from utils.logger import get_logger

logger = get_logger("services.tts", "tts.log")

# ── COSYVoice 路径注入（必须在 import CosyVoice2 之前执行）────────────────
_cosy_dir = str(PathConfig.COSYVOICE_DIR)
_matcha_dir = str(PathConfig.COSYVOICE_DIR / "third_party" / "Matcha-TTS")
for _p in [_cosy_dir, _matcha_dir]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from cosyvoice.cli.cosyvoice import CosyVoice2
    logger.info("COSYVoice 模块导入成功")
except ImportError as e:
    logger.error(f"COSYVoice 导入失败：{e}\n{traceback.format_exc()}")
    CosyVoice2 = None  # type: ignore


class TTSService:
    """
    TTS 服务（单例，由 main.py lifespan 初始化）
    """

    def __init__(self) -> None:
        if CosyVoice2 is None:
            raise RuntimeError("COSYVoice 未能正确导入，TTS 服务无法启动")

        logger.info(f"加载 TTS 模型：{PathConfig.TTS_MODEL_DIR}")
        self._lock = Lock()
        self._model = CosyVoice2(
            str(PathConfig.TTS_MODEL_DIR),
            load_jit=TTSConfig.LOAD_JIT,
            load_trt=TTSConfig.LOAD_TRT,
            fp16=TTSConfig.FP16,
        )

        # 加载参考音频
        if not PathConfig.REFERENCE_AUDIO.exists():
            raise FileNotFoundError(
                f"参考音频不存在：{PathConfig.REFERENCE_AUDIO}\n"
                "请将角色参考音频放置到 resource/voice/ 目录下"
            )
        self._voice_refs = {
            "angry": PathConfig.VOICE_DIR / "NZ_angry.mp3",
            "happy": PathConfig.VOICE_DIR / "NZ_happy.mp3",
        }
        self._ref_texts = {
            "angry": TTSConfig.REFERENCE_TEXT,
            "happy": "你会来吧，因为你是我唯一的朋友啊。一言为定，我等你哦！",
        }
        PathConfig.AUDIO_OUT_DIR.mkdir(parents=True, exist_ok=True)

        logger.info("TTS 服务就绪。")

    def _select_reference_pair(self, text: str) -> tuple[str, str, str]:
        """根据文本情绪选择参考音频与对应参考文本。"""
        sentiment = SnowNLP(text).sentiments
        if sentiment < 1:
            emotion = "angry"
        else:
            emotion = "happy"

        chosen = self._voice_refs[emotion]
        ref_text = self._ref_texts[emotion]
        if not chosen.exists():
            fallback = self._voice_refs["happy" if emotion == "angry" else "angry"]
            fallback_emotion = "happy" if emotion == "angry" else "angry"
            if fallback.exists():
                logger.warning(f"情绪音频 {chosen} 不存在，回退到 {fallback}")
                return str(fallback), self._ref_texts[fallback_emotion], "fallback"
            raise FileNotFoundError(
                f"情绪参考音频都不存在：{self._voice_refs['angry']} / {self._voice_refs['happy']}"
            )

        return str(chosen), ref_text, emotion

    # ── 对外接口 ─────────────────────────────────────────────────────────────

    def synthesize(self, text: str) -> list[Path]:
        """
        将文本合成为语音，返回生成的 WAV 文件路径列表。
        线程安全（GPU 串行推理）。
        """
        if not text.strip():
            raise ValueError("合成文本不能为空")

        saved: list[Path] = []
        prompt_wav, ref_text, emotion = self._select_reference_pair(text)

        with self._lock:
            try:
                results = list(
                    self._model.inference_zero_shot(
                        text,
                        ref_text,
                        prompt_wav,
                        stream=False,
                    )
                )
            except Exception as e:
                logger.error(f"CosyVoice 推理失败：{e}\n{traceback.format_exc()}")
                raise RuntimeError(f"TTS 推理错误：{e}") from e
            finally:
                torch.cuda.empty_cache()

        if not results:
            raise RuntimeError("TTS 引擎返回空结果")

        ts = int(time.time())
        for i, seg in enumerate(results):
            if "tts_speech" not in seg:
                logger.warning(f"片段 {i} 缺少 tts_speech 键，已跳过")
                continue
            wav = seg["tts_speech"].cpu()
            out = PathConfig.AUDIO_OUT_DIR / f"tts_{ts}_{i}.wav"
            torchaudio.save(str(out), wav, self._model.sample_rate)
            saved.append(out)
            logger.debug(f"已保存音频：{out}")

        if not saved:
            raise RuntimeError("所有音频片段均保存失败")

        logger.info(f"合成完成 [{text[:30]}…]，情绪={emotion}，共 {len(saved)} 个文件")
        return saved
