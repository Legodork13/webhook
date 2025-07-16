from flask import Flask, request, jsonify
import os
from telegram import Bot
from telegram.error import TelegramError
from datetime import datetime

app = Flask(__name__)

# Конфигурация
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
INTERNAL_API_KEY = os.getenv('INTERNAL_API_KEY')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

bot = Bot(token=TELEGRAM_BOT_TOKEN)

def log(message, level='INFO'):
    """Логирование с временной меткой"""
    if LOG_LEVEL == 'DEBUG' or level in ('ERROR', 'WARNING'):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] {message}")

@app.route('/api/bot', methods=['POST'])
def handle_bot_notification():
    try:
        # Базовая проверка авторизации
        auth_header = request.headers.get('Authorization')
        if auth_header != f"Bearer {INTERNAL_API_KEY}":
            log("Invalid internal API key", 'WARNING')
            return jsonify({"error": "Unauthorized"}), 401

        data = request.get_json()
        if not data:
            log("Empty notification data", 'WARNING')
            return jsonify({"error": "No data provided"}), 400

        message = data.get('message')
        if not message:
            # Автоформатирование если сообщение не предоставлено
            original = data.get('original_data', {})
            message = (
                "🔔 Новое уведомление\n\n"
                f"📅 {datetime.fromisoformat(data['timestamp']).strftime('%d.%m.%Y %H:%M')}\n"
                f"📊 Данные: {str(original)[:200]}..."
            )

        log(f"Sending to Telegram: {message[:100]}...", 'DEBUG')
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        
        return jsonify({"status": "sent"}), 200

    except TelegramError as e:
        log(f"Telegram error: {str(e)}", 'ERROR')
        return jsonify({"error": "Telegram delivery failed"}), 500
    except Exception as e:
        log(f"Unexpected error: {str(e)}", 'ERROR')
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5001)))