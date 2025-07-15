from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

TOKENVIEW_API_KEY = os.getenv('TOKENVIEW_API_KEY')
VERCEL_URL = os.getenv('VERCEL_URL')

@app.route('/api/webhook', methods=['GET', 'POST'])
def handle_webhook():
    if request.method == 'GET':
        # Tokenview проверяет URL - просто возвращаем успешный статус
        return jsonify({"status": "OK", "message": "Webhook is ready"}), 200
    
    elif request.method == 'POST':
        try:
            # Проверка подписи
            signature = request.headers.get('X-Tokenview-Signature')
            if not signature or signature != TOKENVIEW_API_KEY:
                return jsonify({"error": "Invalid signature"}), 401

            data = request.json
            
            # Обработка разных типов событий
            event_handlers = {
                'transaction': handle_transaction,
                'token_create': handle_token_create,
                'whale_alert': handle_whale_alert,
                'web3_event': handle_web3_event
            }
            
            handler = event_handlers.get(data.get('type'))
            if handler:
                return handler(data)
            return jsonify({"error": "Unknown event type"}), 400

        except Exception as e:
            print(f"Error processing webhook: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500

    else:
        return jsonify({"error": "Method not allowed"}), 405

def handle_transaction(data):
    # Формируем сообщение о транзакции
    message = (
        f"🔔 Новая транзакция (ETH):\n\n"
        f"📝 Хеш: {data.get('hash', 'N/A')}\n"
        f"📦 Блок: {data.get('block_number', 'N/A')}\n"
        f"📤 От: {data.get('from', 'N/A')}\n"
        f"📥 Кому: {data.get('to', 'N/A')}\n"
        f"💰 Сумма: {data.get('value', '0')} ETH\n"
        f"⏱ Время: {data.get('timestamp', 'N/A')}"
    )
    
    # Отправляем в Telegram через наш бот
    bot_response = requests.post(
        f"{VERCEL_URL}/api/bot",
        json={
            "type": "transaction",
            "message": message,
            "original_data": data
        }
    )
    
    if bot_response.status_code == 200:
        return jsonify({"status": "Transaction processed"}), 200
    return jsonify({"error": "Failed to send to Telegram"}), 500

# ... (остальные обработчики handle_token_create, handle_whale_alert, handle_web3_event остаются без изменений)

if __name__ == '__main__':
    app.run()