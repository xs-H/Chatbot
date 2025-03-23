from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import logging
import os
import time
import torch
import torchaudio
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
from chat import ChatSystem
import uuid

# Configure logging
if not os.path.exists('./log'):
    os.makedirs('./log')
logging.basicConfig(
    filename='./log/api.log',
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# 创建存放语音文件的目录
if not os.path.exists('./audio_output'):
    os.makedirs('./audio_output')

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize chat system
chat_system = None
try:
    chat_system = ChatSystem()
    logging.info("Chat system initialized successfully")
except Exception as e:
    logging.critical(f"Failed to initialize chat system: {str(e)}")

# 初始化TTS模型
tts_model = None
try:
    print("Loading TTS model...")
    config = XttsConfig()
    config.load_json(r"C:\Users\lenovo\AppData\Local\tts\tts_models--multilingual--multi-dataset--xtts_v2\config.json")
    tts_model = Xtts.init_from_config(config)
    tts_model.load_checkpoint(config,
                              checkpoint_dir=r"C:\Users\lenovo\AppData\Local\tts\tts_models--multilingual--multi-dataset--xtts_v2",
                              use_deepspeed=False)
    tts_model.cuda()

    # 预先计算说话人特征
    print("Computing speaker latents...")
    gpt_cond_latent, speaker_embedding = tts_model.get_conditioning_latents(
        audio_path=[r"E:\OneDrive\桌面\入党申请书\zh_combine.mp3"])

    # 将说话人特征保存为全局变量供后续使用
    app.config['GPT_COND_LATENT'] = gpt_cond_latent
    app.config['SPEAKER_EMBEDDING'] = speaker_embedding

    logging.info("TTS model initialized successfully")
except Exception as e:
    logging.critical(f"Failed to initialize TTS model: {str(e)}")


def generate_speech(text):
    """将文本转换为语音，并返回保存的文件路径"""
    try:
        if tts_model is None:
            logging.error("TTS model not initialized")
            return None

        # 生成唯一的文件名
        filename = f"speech_{uuid.uuid4()}.wav"
        filepath = os.path.join('./audio_output', filename)

        time_start = time.perf_counter()
        out = tts_model.inference(
            text,
            "zh-cn",
            app.config['GPT_COND_LATENT'],
            app.config['SPEAKER_EMBEDDING'],
            temperature=0.7
        )
        torchaudio.save(filepath, torch.tensor(out["wav"]).unsqueeze(0), 24000)
        time_end = time.perf_counter()

        logging.info(f"Speech generated in {time_end - time_start} seconds: {filepath}")
        return filepath
    except Exception as e:
        logging.error(f"Error generating speech: {str(e)}")
        return None


@app.route('/api/chat', methods=['POST'])
def chat():
    if chat_system is None:
        return jsonify({"error": "Chat system is not initialized"}), 500

    try:
        data = request.json
        user_message = data.get('message', '')

        if not user_message.strip():
            return jsonify({"error": "Empty message"}), 400

        # Get context for the query
        context = chat_system.text_embedding._retrieve_context(f"{user_message}+哪吒台词")

        # Format messages
        messages = chat_system._format_messages(user_message, context)

        # Generate response
        response = chat_system.client.chat(
            model=chat_system.model_name,
            messages=messages
        )

        # Extract reply
        reply = response['message']['content'].lstrip('\n')

        # Update conversation history
        chat_system.conversation_history.extend([
            {'role': 'user', 'content': user_message},
            {'role': 'assistant', 'content': reply}
        ])

        # 生成语音文件
        speech_file = generate_speech(reply)

        # Log the interaction
        logging.info(f"Query: {user_message}")
        logging.info(f"Reply: {reply}")

        response_data = {
            "reply": reply
        }

        # 如果成功生成语音，添加语音文件路径到响应
        if speech_file:
            response_data["audio_path"] = f"/api/audio/{os.path.basename(speech_file)}"

        return jsonify(response_data)

    except Exception as e:
        logging.error(f"Error processing chat request: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/api/audio/<filename>', methods=['GET'])
def get_audio(filename):
    """提供生成的音频文件下载"""
    try:
        filepath = os.path.join('./audio_output', filename)
        if os.path.exists(filepath):
            return send_file(filepath, mimetype="audio/wav", as_attachment=True)
        else:
            return jsonify({"error": "Audio file not found"}), 404
    except Exception as e:
        logging.error(f"Error serving audio file: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/api/reset', methods=['POST'])
def reset_conversation():
    try:
        chat_system.conversation_history = []
        return jsonify({"status": "success", "message": "Conversation history reset"})
    except Exception as e:
        logging.error(f"Error resetting conversation: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=False)