from flask import Flask, request, jsonify
import os
import requests
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def make_bot_request(data):
    """Безопасный вызов Telegram бота"""
    bot_url = f"{os.getenv('VERCEL_URL').strip('/')}/api/bot"
    headers = {
        'Authorization': f'Bearer {os.getenv("INTERNAL_API_KEY")}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            bot_url,
            json={
                "transaction": data,
                "metadata": {
                    "source": "tokenview",
                    "received_at": datetime.now().isoformat()
                }
            },
            headers=headers,
            timeout=5
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Bot request failed: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Bot response: {e.response.text}")
        return False

@app.route('/api/webhook', methods=['POST'])
def handle_webhook():
    try:
        data = request.get_json()
        logger.info(f"Received transaction: {data.get('txid')}")
        
        if not make_bot_request(data):
            return jsonify({"error": "Bot service unavailable"}), 502
            
        return jsonify({"status": "processed"}), 200

    except Exception as e:
        logger.exception("Webhook processing failed")
        return jsonify({"error": "Internal server error"}), 500