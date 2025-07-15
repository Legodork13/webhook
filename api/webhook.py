from flask import Flask, request, jsonify
import os
import requests
from datetime import datetime

app = Flask(__name__)

# Конфигурация
TOKENVIEW_API_KEY = os.getenv('TOKENVIEW_API_KEY')
VERCEL_URL = os.getenv('VERCEL_URL')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')  # DEBUG, INFO, WARNING, ERROR

def log(message, level='INFO'):
    """Логирование с временной меткой"""
    if LOG_LEVEL == 'DEBUG' or level in ('ERROR', 'WARNING'):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] {message}")

@app.route('/api/webhook', methods=['GET', 'POST'])
def handle_webhook():
    try:
        # Логируем входящий запрос
        log(f"Incoming request: {request.method} {request.url}")
        log(f"Headers: {dict(request.headers)}", 'DEBUG')
        
        if request.method == 'GET':
            log("GET verification request received")
            return jsonify({
                "status": "OK",
                "message": "Webhook is ready",
                "timestamp": datetime.now().isoformat()
            }), 200

        elif request.method == 'POST':
            # Проверка подписи (с поддержкой разных вариантов заголовка)
            signature = (
                request.headers.get('X-Tokenview-Signature') or 
                request.headers.get('Tokenview-Signature') or 
                request.headers.get('X-Signature')
            )
            
            if not signature:
                log("No signature header found", 'WARNING')
                # return jsonify({"error": "Signature required"}), 401  # Раскомментируйте для строгой проверки
            
            if signature and signature != TOKENVIEW_API_KEY:
                log(f"Invalid signature. Received: {signature}", 'ERROR')
                return jsonify({
                    "error": "Invalid signature",
                    "received_signature": signature[:6] + "..." if signature else None,
                    "expected_length": len(TOKENVIEW_API_KEY) if TOKENVIEW_API_KEY else 0
                }), 401

            # Обработка тела запроса
            data = request.get_json()
            if not data:
                log("Empty request body", 'WARNING')
                return jsonify({"error": "No data provided"}), 400

            log(f"Received data: {data}", 'DEBUG')
            
            # Здесь можно добавить обработку разных типов событий
            response = {
                "status": "processed",
                "event_type": data.get('type'),
                "timestamp": datetime.now().isoformat()
            }
            
            # Отправляем в Telegram бот
            bot_response = requests.post(
                f"{VERCEL_URL}/api/bot",
                json={
                    "source": "tokenview",
                    "original_data": data,
                    "processed_at": datetime.now().isoformat()
                },
                timeout=5
            )
            
            if bot_response.status_code != 200:
                log(f"Telegram bot error: {bot_response.text}", 'ERROR')
            
            return jsonify(response), 200

    except Exception as e:
        log(f"Unexpected error: {str(e)}", 'ERROR')
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))