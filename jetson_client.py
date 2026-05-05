"""
Jetson 端客户端脚本
- 通过 HTTP 与 AutoDL 服务器通信
- 负责：录音 → ASR → Chat → TTS → 播放
- 依赖：pip install requests sounddevice soundfile numpy
"""
from __future__ import annotations

import io
import os
import sys
import tempfile
import time
import wave

import numpy as np
import requests
import sounddevice as sd
import soundfile as sf

# ── 配置 ─────────────────────────────────────────────────────────────────────
# 替换为 AutoDL 实例的公网地址和端口（控制台 → 自定义服务 → 映射端口）
SERVER_URL  = os.getenv("CHATBOT_SERVER", "http://<AutoDL_IP>:<PORT>")
SESSION_ID  = "jetson_default"

# 录音参数
SAMPLE_RATE  = 16000
CHANNELS     = 1
RECORD_SECS  = 5      # 每次录音最大秒数（按 Enter 可提前结束）

# ── HTTP 工具 ─────────────────────────────────────────────────────────────────

def check_server() -> bool:
    try:
        r = requests.get(f"{SERVER_URL}/health", timeout=5)
        data = r.json()
        print(f"[健康检查] {data}")
        return r.status_code == 200
    except Exception as e:
        print(f"[错误] 无法连接服务器：{e}")
        return False


def asr(audio_bytes: bytes, suffix: str = ".wav") -> str:
    r = requests.post(
        f"{SERVER_URL}/api/asr",
        files={"file": (f"audio{suffix}", audio_bytes, "audio/wav")},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["text"]


def chat(message: str) -> str:
    r = requests.post(
        f"{SERVER_URL}/api/chat",
        json={"message": message, "session_id": SESSION_ID},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["reply"]


def tts(text: str) -> bytes | None:
    """合成语音，返回第一个 WAV 的原始字节"""
    r = requests.post(
        f"{SERVER_URL}/api/tts",
        json={"text": text},
        timeout=60,
    )
    r.raise_for_status()
    files = r.json().get("audio_files", [])
    if not files:
        return None
    audio_r = requests.get(f"{SERVER_URL}/api/tts/audio/{files[0]}", timeout=30)
    audio_r.raise_for_status()
    return audio_r.content


def play_wav(wav_bytes: bytes) -> None:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(wav_bytes)
        tmp_path = tmp.name
    try:
        data, sr = sf.read(tmp_path)
        sd.play(data, sr)
        sd.wait()
    finally:
        os.unlink(tmp_path)


def record_audio(seconds: int = RECORD_SECS) -> bytes:
    """录制 WAV，返回原始字节"""
    print(f"[录音] 开始，最长 {seconds} 秒，录完后按 Enter…")
    frames = sd.rec(
        int(seconds * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
    )
    input()           # 阻塞直到用户按 Enter
    sd.stop()
    audio_data = frames[: len(frames)]   # 取已录部分

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)              # int16 = 2 bytes
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_data.tobytes())
    return buf.getvalue()


# ── 主循环 ────────────────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("  哪吒对话终端  (输入 'exit' 退出，'reset' 重置会话)")
    print("=" * 50)

    if not check_server():
        sys.exit(1)

    while True:
        print("\n[输入方式] 1=文字  2=语音  q=退出")
        mode = input(">>> ").strip().lower()

        if mode in ("q", "exit", "quit"):
            print("再见！")
            break

        if mode == "reset":
            try:
                requests.post(
                    f"{SERVER_URL}/api/chat/reset",
                    json={"session_id": SESSION_ID},
                    timeout=5,
                )
                print("[会话已重置]")
            except Exception as e:
                print(f"[重置失败] {e}")
            continue

        # ── 获取文本输入 ─────────────────────────────────────────────────────
        if mode == "2":
            wav_bytes = record_audio()
            print("[识别中…]")
            try:
                user_text = asr(wav_bytes)
                print(f"[识别结果] {user_text}")
            except Exception as e:
                print(f"[ASR 失败] {e}")
                continue
        else:
            user_text = input("你：").strip()
            if not user_text:
                continue

        # ── Chat ─────────────────────────────────────────────────────────────
        print("[思考中…]")
        try:
            reply = chat(user_text)
        except Exception as e:
            print(f"[Chat 失败] {e}")
            continue
        print(f"哪吒：{reply}")

        # ── TTS + 播放 ───────────────────────────────────────────────────────
        print("[合成语音…]")
        try:
            wav = tts(reply)
            if wav:
                play_wav(wav)
        except Exception as e:
            print(f"[TTS 失败] {e}")


if __name__ == "__main__":
    main()
