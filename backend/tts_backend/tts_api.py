from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import logging
import os
from threading import Lock


# 设置锁
model_lock = Lock()

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
import torchaudio
import torch
torch.cuda.empty_cache()
import time
import sys
import traceback
from pathlib import Path
import onnxruntime


cosyvoice = None

def get_cosyvoice_instance():
    global cosyvoice
    if cosyvoice is None:
        model_path = os.path.join(dir_path, 'pretrained_models/CosyVoice2-0.5B')
        logging.info(f"Initializing CosyVoice2 with model path: {model_path}")

        if not os.path.exists(model_path):
            logging.error(f"Model directory not found at: {model_path}")
            sys.exit(1)

        cosyvoice = CosyVoice2(
            model_path,
            load_jit = False,
            load_trt = False,
            fp16 = False
        )
        logging
    return cosyvoice





# 配置详细日志
logging.basicConfig(
    filename='../../logs/tts_api.log',
    level=logging.DEBUG,  # 使用DEBUG级别获取更详细的日志
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# 创建控制台处理器以便在终端也看到日志
if not any(isinstance(handler, logging.StreamHandler) for handler in logging.getLogger().handlers):
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)

logging.info("Starting TTS API service...")

# 检查ONNX运行时提供者
providers = onnxruntime.get_available_providers()
logging.info(f"Available ONNX providers: {providers}")

# 设置路径
try:
    dir_path = os.path.abspath("./COSYVoice")
    logging.info(f"COSYVoice directory path: {dir_path}")

    sys.path.append(os.path.join(dir_path, "third_party/Matcha-TTS"))
    sys.path.append(dir_path)
    # 导入 cosyvoice 类
    from COSYVoice.cosyvoice.cli.cosyvoice import CosyVoice2
    from COSYVoice.cosyvoice.utils.file_utils import load_wav

    logging.info("Successfully imported COSYVoice modules")
except Exception as e:
    logging.error(f"Error importing modules: {str(e)}")
    logging.error(traceback.format_exc())
    sys.exit(1)


# 确保音频存储目录存在
AUDIO_DIR = "./generated_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)
logging.info(f"Audio storage directory: {os.path.abspath(AUDIO_DIR)}")


app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 查找参考音频文件
try:
    current_file = Path(__file__).resolve()
    logging.info(f"Current file path: {current_file}")

    # 尝试不同的路径找到参考音频
    possible_paths = [
        current_file.parents[2] / 'resource' / 'voice' / "NZ_angry.mp3",  # 项目根目录
        # Path("./resource/voice/NeZha''.mp3"),  # 相对当前目录
        # Path(os.path.abspath("../resource/voice/NeZha''.mp3")),  # 上一级目录
        # Path(os.path.abspath("../../resource/voice/NeZha''.mp3")),  # 上两级目录
    ]

    mp3_path = None
    for path in possible_paths:
        logging.info(f"Checking for reference audio at: {path}")
        if path.exists():
            mp3_path = path
            logging.info(f"Found reference audio at: {mp3_path}")
            break

    if mp3_path is None:
        logging.error("Reference audio file not found in any of the expected locations")
        # 创建一个提示用户的错误信息，但不退出程序
        reference_error = "Reference audio file not found. API will fail on TTS requests."
    else:
        # 加载参考音频
        try:
            prompt_speech_16k = load_wav(mp3_path, 16000)
            logging.info("Reference audio loaded successfully")
            reference_error = None
        except Exception as e:
            logging.error(f"Failed to load reference audio: {str(e)}")
            logging.error(traceback.format_exc())
            reference_error = f"Failed to load reference audio: {str(e)}"
except Exception as e:
    logging.error(f"Error while searching for reference audio: {str(e)}")
    logging.error(traceback.format_exc())
    reference_error = f"Error setting up reference audio: {str(e)}"

# 参考音频的文本内容
REFERENCE_TEXT = "拜个屁的师我什么都不学！修炼了出去捧那些白痴的臭脚，还不如在这睡大觉。"

######################### 初始化 CosyVoice2 #######################################
get_cosyvoice_instance()
######################### 初始化 CosyVoice2 #######################################

@app.route('/api/tts', methods=['POST'])
def tts():
    try:

        if reference_error:
            logging.error(f"TTS request failed due to reference audio error: {reference_error}")
            return jsonify({"error": reference_error}), 500

        data = request.json
        if not data:
            logging.error("No JSON data received in request")
            return jsonify({"error": "No JSON data provided"}), 400

        text = data.get("text", "")
        # reference_text = data.get("reference_text", REFERENCE_TEXT)

        if not text:
            logging.error("Missing text input in request")
            return jsonify({"error": "Missing text input"}), 400

        logging.info(f"TTS Request - Text: {text}")
        # logging.info(f"Using reference text: {reference_text}")

        # 生成语音
        audio_files = []
        # print(type(text))
        # print(text)
        inference_result = cosyvoice.inference_zero_shot(
            text,
            REFERENCE_TEXT,
            prompt_speech_16k,
            stream=False
        )
        inference_result = list(inference_result)

        if not inference_result:
            logging.error("TTS engine returned empty result")
            return jsonify({"error": "TTS engine returned no data"}), 500

        logging.info(f"TTS inference completed, processing {len(inference_result)} audio segments")

        for i, result in enumerate(inference_result):
            if 'tts_speech' not in result:
                logging.error(f"Missing tts_speech in result segment {i}")
                continue

            result['tts_speech'] = result['tts_speech'].cpu()

            file_name = f"tts_{int(time.time())}_{i}.wav"
            # 音频文件保存
            file_path = os.path.join(AUDIO_DIR, file_name)

            try:
                torchaudio.save(file_path, result['tts_speech'], cosyvoice.sample_rate)
                logging.info(f"Saved audio file: {file_path}")
                audio_files.append(file_name)
            except Exception as e:
                logging.error(f"Failed to save audio file {file_path}: {str(e)}")
                logging.error(traceback.format_exc())

        if not audio_files:
            logging.error("No audio files were generated")
            return jsonify({"error": "Failed to generate audio files"}), 500

        logging.info(f"Generated {len(audio_files)} audio files: {audio_files}")
        return jsonify({"audio_files": audio_files})

    except Exception as e:
        logging.error(f"TTS Error: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

    finally:
        torch.cuda.empty_cache()


@app.route('/api/audio/<filename>', methods=['GET'])
def get_audio(filename):
    file_path = os.path.join(AUDIO_DIR, filename)
    logging.info(f"Request for audio file: {file_path}")

    if os.path.exists(file_path):
        logging.info(f"Sending audio file: {file_path}")
        return send_file(file_path, mimetype="audio/wav")

    logging.error(f"Audio file not found: {file_path}")
    return jsonify({"error": "File not found"}), 404


@app.route('/api/status', methods=['GET'])
def status():
    """API状态检查端点，用于验证服务是否正常运行"""
    return jsonify({
        "status": "running",
        "reference_audio": "loaded" if not reference_error else "error",
        "error": reference_error,
        "audio_dir": os.path.abspath(AUDIO_DIR)
    })


if __name__ == '__main__':
    logging.info("Starting Flask server on port 5001")
    app.run(host='0.0.0.0', port=5001, debug=False)
