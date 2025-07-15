from flask import Flask, request, jsonify
import os
from telegram import Bot
from telegram.error import TelegramError

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

bot = Bot(token=TELEGRAM_BOT_TOKEN)

@app.route('/api/bot', methods=['POST'])
def handle_bot_notification():
    if request.method != 'POST':
        return jsonify({"error": "Method not allowed"}), 405

    try:
        data = request.json
        message = data.get('message')
        
        if not message:
            return jsonify({"error": "No message provided"}), 400

        # Отправляем сообщение в Telegram
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='Markdown'
        )
        
        return jsonify({"status": "Notification sent"}), 200

    except TelegramError as e:
        print(f"Telegram error: {str(e)}")
        return jsonify({"error": "Failed to send Telegram message"}), 500
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run()