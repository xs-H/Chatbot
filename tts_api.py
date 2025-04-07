from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import logging
import os
import torchaudio
import time
import sys

dir_path=r"D:\HJG\500.Projects\chatbot-v1\backend\tts_backend\COSYVoice"
sys.path.append(dir_path+r"\third_party\Matcha-TTS")
sys.path.append(dir_path)
from COSYVoice.cosyvoice.cli.cosyvoice import CosyVoice2

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

# 初始化 CosyVoice2
cosyvoice = CosyVoice2(
    dir_path + r"\pretrained_models\CosyVoice2-0.5B",
    load_jit=False,
    load_trt=False,
    fp16=False
)

# 确保音频存储目录存在
AUDIO_DIR = "./generated_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

@app.route('/api/tts', methods=['POST'])
def tts():
    try:
        data = request.json
        text = data.get("text", "")
        reference_text = data.get("reference_text", "")
        prompt_audio = "your_prompt_audio_file.wav"  # 这里换成实际的音频文件

        if not text:
            return jsonify({"error": "Missing text input"}), 400

        # 生成语音
        audio_files = []
        for i, j in enumerate(cosyvoice.inference_zero_shot(text, reference_text, prompt_audio, stream=False)):
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