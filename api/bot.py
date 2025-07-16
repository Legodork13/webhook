from flask import Flask, request, jsonify
import os
from telegram import Bot
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_auth():
    """Проверка авторизации с подробным логированием"""
    expected = f'Bearer {os.getenv("INTERNAL_API_KEY")}'
    received = request.headers.get('Authorization')
    
    if not received:
        logger.error("Missing Authorization header")
        return False
        
    if received != expected:
        logger.error(f"Invalid auth. Expected: {expected[:15]}..., Received: {received[:15]}...")
        return False
        
    return True

@app.route('/api/bot', methods=['POST'])
def handle_bot_notification():
    if not verify_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        data = request.json
        logger.info(f"Processing bot request: {data.get('transaction', {}).get('txid')}")
        
        # Ваша логика отправки в Telegram
        bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
        bot.send_message(
            chat_id=os.getenv('TELEGRAM_CHAT_ID'),
            text=f"New transaction: {data['transaction']['txid'][:10]}..."
        )
        
        return jsonify({"status": "sent"}), 200
        
    except Exception as e:
        logger.exception("Bot processing failed")
        return jsonify({"error": str(e)}), 500