from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
from chat import ChatSystem
import pynvml
handle = pynvml.nvmlDeviceGetHandleByIndex(0)

# Configure logging
if not os.path.exists('./log'):
    os.makedirs('./log')
logging.basicConfig(
    filename='./log/api.log',
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize chat system
chat_system = None
try:
    chat_system = ChatSystem()
    logging.info("Chat system initialized successfully")
except Exception as e:
    logging.critical(f"Failed to initialize chat system: {str(e)}")


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
        print(f"显存占用：{pynvml.nvmlDeviceGetMemoryInfo(handle).used/1024**3}GB")


        # Extract reply
        reply = response['message']['content'].lstrip('\n')

        # Update conversation history
        chat_system.conversation_history.extend([
            {'role': 'user', 'content': user_message},
            {'role': 'assistant', 'content': reply}
        ])

        # Log the interaction
        logging.info(f"Query: {user_message}")
        logging.info(f"Reply: {reply}")

        return jsonify({"reply": reply})

    except Exception as e:
        logging.error(f"Error processing chat request: {str(e)}")
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
    print("Starting server...")
    app.run(host='0.0.0.0', port=3000, debug=True)
    print("Server started")
    # app.run(host='0.0.0.0', port=3000, debug=False)
