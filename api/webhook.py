from flask import Flask, request, jsonify
import os
import requests
from datetime import datetime

app = Flask(__name__)

# Конфигурация
TOKENVIEW_API_KEY = os.getenv('TOKENVIEW_API_KEY')
VERCEL_URL = os.getenv('VERCEL_URL', '').rstrip('/')
ALLOW_UNSIGNED = os.getenv('ALLOW_UNSIGNED', 'false').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

def log(message, level='INFO'):
    """Логирование с временной меткой"""
    if LOG_LEVEL == 'DEBUG' or level in ('ERROR', 'WARNING'):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] {message}")

def ensure_https(url):
    """Добавляет схему к URL если отсутствует"""
    if not url.startswith(('http://', 'https://')):
        return f'https://{url}'
    return url

@app.route('/api/webhook', methods=['GET', 'POST'])
def handle_webhook():
    try:
        if request.method == 'GET':
            log("GET verification request received")
            return jsonify({"status": "ready"}), 200

        # Проверка подписи
        signature = request.headers.get('X-Tokenview-Signature')
        
        if not signature and not ALLOW_UNSIGNED:
            log("No signature header and ALLOW_UNSIGNED=false", 'WARNING')
            return jsonify({"error": "Signature header required"}), 401
            
        if signature and signature != TOKENVIEW_API_KEY:
            log(f"Invalid signature (received: {signature[:6]}...)", 'ERROR')
            return jsonify({"error": "Invalid signature"}), 401

        data = request.get_json()
        if not data:
            log("Empty request body", 'WARNING')
            return jsonify({"error": "No data provided"}), 400

        log(f"Received data: {data}", 'DEBUG')
        
        # Формирование сообщения (адаптируйте под ваш формат)
        tx_hash = data.get('ar') or data.get('hash') or 'N/A'
        status = data.get('status', 'unknown')
        message = (
            "🔔 Новое уведомление\n\n"
            f"🆔 Хеш: {tx_hash[:12]}...\n"
            f"✅ Статус: {status}\n"
            f"⏱ Время: {datetime.now().strftime('%H:%M:%S')}"
        )

        # Отправка в Telegram бота
        bot_url = ensure_https(f"{VERCEL_URL}/api/bot")
        payload = {
            "message": message,
            "original_data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            response = requests.post(bot_url, json=payload, timeout=5)
            response.raise_for_status()
            log("Notification forwarded to bot", 'DEBUG')
        except requests.exceptions.RequestException as e:
            log(f"Failed to forward to bot: {str(e)}", 'ERROR')
            return jsonify({"error": "Bot forwarding failed"}), 500

        return jsonify({"status": "processed"}), 200

    except Exception as e:
        log(f"Unexpected error: {str(e)}", 'ERROR')
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))