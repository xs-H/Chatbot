from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import logging
import os
import torchaudio
import time
import sys
from pathlib import Path

# 添加项目路径
dir_path = r".\\COSYVoice"
sys.path.append(dir_path + r"\\third_party\\Matcha-TTS")
sys.path.append(dir_path)

from COSYVoice.cosyvoice.cli.cosyvoice import CosyVoice2
from COSYVoice.cosyvoice.utils.file_utils import load_wav

# 配置日志
if not os.path.exists('../../logs'):
    os.makedirs('../../logs')
logging.basicConfig(
    filename='../../logs/tts_api.log',
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 初始化 CosyVoice2（ONNX 不再需要）
cosyvoice = CosyVoice2(
    dir_path + r"\\pretrained_models\\CosyVoice2-0.5B",
    load_jit=False,
    load_trt=False,
    fp16=False
)

# 音频输出目录
AUDIO_DIR = "./generated_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

# 加载参考音频
current_file = Path(__file__).resolve()
project_root = current_file.parents[2]  # 根目录推断
mp3_path = project_root / 'resource' / 'voice' / "NeZha'.mp3"
prompt_speech_16k = load_wav(mp3_path, 16000)

# 默认参考文本
REFERENCE_TEXT = "拜个屁的师我什么都不学！修炼了出去捧那些白痴的臭脚，还不如在这睡大觉。"

@app.route('/api/tts', methods=['POST'])
def tts():
    try:
        data = request.json
        text = data.get("text", "")
        reference_text = data.get("reference_text", REFERENCE_TEXT)

        if not text:
            return jsonify({"error": "Missing text input"}), 400

        logging.info(f"TTS Request - Text: {text}")

        # 语音生成
        audio_files = []
        for i, j in enumerate(cosyvoice.inference_zero_shot(text, reference_text, prompt_speech_16k, stream=False)):
            file_name = f"{AUDIO_DIR}/tts_{int(time.time())}_{i}.wav"
            torchaudio.save(file_name, j['tts_speech'], cosyvoice.sample_rate)
            audio_files.append(file_name)

        logging.info(f"Generated audio files: {audio_files}")
        return jsonify({"audio_files": audio_files})

    except Exception as e:
        logging.error(f"TTS Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/audio/<filename>', methods=['GET'])
def get_audio(filename):
    file_path = os.path.join(AUDIO_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, mimetype="audio/wav")
    return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)