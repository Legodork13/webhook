from flask import Flask, request, jsonify
import os
import requests
from datetime import datetime  # Добавлен недостающий импорт
import logging

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def make_bot_request(data):
    """Безопасный вызов Telegram бота"""
    try:
        bot_url = f"{os.getenv('VERCEL_URL', '').rstrip('/')}/api/bot"
        headers = {
            'Authorization': f'Bearer {os.getenv('INTERNAL_API_KEY')}',
            'Content-Type': 'application/json'
        }
        
        logger.info(f"Calling bot at: {bot_url}")
        
        response = requests.post(
            bot_url,
            json={
                "transaction": data,
                "timestamp": datetime.now().isoformat()  # Теперь datetime доступен
            },
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Bot request failed: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response: {e.response.text}")
        return False

@app.route('/api/webhook', methods=['POST'])
def handle_webhook():
    try:
        data = request.get_json()
        if not data:
            logger.error("Empty request received")
            return jsonify({"error": "Empty request"}), 400
            
        logger.info(f"Processing tx: {data.get('txid', 'unknown')}")
        
        if not make_bot_request(data):
            return jsonify({"error": "Bot service unavailable"}), 502
            
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        logger.exception("Critical error in webhook")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)