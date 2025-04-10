from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import logging
import os
import torchaudio
import time
import sys
from pathlib import  Path
import onnxruntime


# 初始化跨平台兼容路径
current_dir = os.path.dirname(os.path.abspath(__file__))  # 获取当前脚本绝对路径
dir_path = os.path.join(current_dir, "COSYVoice")
sys.path.append(os.path.join(dir_path, "third_party", "Matcha-TTS"))
sys.path.append(dir_path)

# ONNX初始化必须在导入COSYVoice模块之前
onnxruntime.get_available_providers()
onnx_session = onnxruntime.InferenceSession(
    os.path.join(dir_path, "pretrained_models", "CosyVoice2-0.5B", "speech_tokenizer_v2.onnx"),
    providers=["CUDAExecutionProvider"]
)

# 配置日志
log_dir = os.path.join(current_dir, "..", "..", "logs")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "tts_api.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True  # 覆盖可能存在的旧配置
)

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 初始化 CosyVoice2
from COSYVoice.cosyvoice.cli.cosyvoice import CosyVoice2
from COSYVoice.cosyvoice.utils.file_utils import load_wav

cosyvoice = CosyVoice2(
    os.path.join(dir_path, "pretrained_models", "CosyVoice2-0.5B"),
    load_jit=False,
    load_trt=False,
    fp16=False
)

# 音频存储目录（使用绝对路径）
AUDIO_DIR = os.path.join(current_dir, "generated_audio")
os.makedirs(AUDIO_DIR, exist_ok=True)
logging.info(f"Audio storage directory: {AUDIO_DIR}")

# 加载参考音频
project_root = Path(current_dir).parents[2]  # 向上追溯两级目录
mp3_path = project_root / 'resource' / 'voice' / "NeZha''.mp3"
try:
    prompt_speech_16k = load_wav(mp3_path, 16000)
    logging.info("Reference audio loaded successfully")
except Exception as e:
    logging.error(f"Failed to load reference audio: {str(e)}")
    raise

# 参考音频的文本内容
REFERENCE_TEXT = "拜个屁的师我什么都不学！修炼了出去捧那些白痴的臭脚，还不如在这睡大觉。"

@app.route('/api/tts', methods=['POST'])
def tts():
    try:
        data = request.json
        text = data.get("text", "")
        # 使用参考文本
        reference_text = data.get("reference_text", REFERENCE_TEXT)


        if not text:
            logging.warning("Received empty text input")
            return jsonify({"error": "Missing text input"}), 400

        logging.info(f"TTS Request - Text: {text}")

        # 生成语音
        audio_files = []
        for i, j in enumerate(cosyvoice.inference_zero_shot(text, reference_text, prompt_speech_16k, stream=False)):
            try:
                # 验证音频张量
                if j['tts_speech'].numel() == 0:
                    raise ValueError("Empty audio tensor received")

                # 生成绝对路径文件名
                timestamp = int(time.time())
                file_name = os.path.join(AUDIO_DIR, f"tts_{timestamp}_{i}.wav")
                logging.info(f"Saving audio to: {file_name}")
                logging.debug(f"Tensor shape: {j['tts_speech'].shape}")

                torchaudio.save(file_name, j['tts_speech'], cosyvoice.sample_rate)
                if os.path.exists(file_name):
                    audio_files.append(file_name)
                    logging.info(f"File saved successfully: {file_name}")
                else:
                    logging.error(f"File not created: {file_name}")
            except Exception as inner_e:
                logging.error(f"Error saving audio segment {i}: {str(inner_e)}")
                continue

        # 以下内容在循环外
        if not audio_files:
            logging.error("No audio files generated")
            return jsonify({"error": "Failed to generate audio"}), 500

        logging.info(f"Generated {len(audio_files)} files")
        return jsonify({"audio_files": [os.path.basename(f) for f in audio_files]})  # 返回文件名列表

    except Exception as e:
        logging.error(f"TTS Error: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/audio/<filename>', methods=['GET'])
def get_audio(filename):
    try:
        file_path = os.path.join(AUDIO_DIR, filename)
        if not os.path.exists(file_path):
            logging.warning(f"File not found: {filename}")
            return jsonify({"error": "File not found"}), 404

        logging.info(f"Serving audio file: {filename}")
        return send_file(file_path, mimetype="audio/wav")
    except Exception as e:
        logging.error(f"Audio serve error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logging.info("Starting TTS API server")
    app.run(host='0.0.0.0', port=5001, debug=True)
