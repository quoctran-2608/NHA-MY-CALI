from flask import Flask, request, Response
import requests
import hmac
import hashlib
import json
import os

app = Flask(__name__)

# Biến cấu hình (dùng env vars cho bảo mật)
FB_VERIFY_TOKEN = os.getenv('FB_VERIFY_TOKEN', 'mysecret')
FB_APP_SECRET = os.getenv('FB_APP_SECRET', 'your_facebook_app_secret')
ZALO_BOT_TOKEN = os.getenv('ZALO_BOT_TOKEN', '1087363824973385617:crKKlfdMIEFnfJmmnRhTdczBYkEmYmzDhCciTLeyglWuqKonGKchjaCiztxfZiZp')
ZALO_CHAT_ID = os.getenv('ZALO_CHAT_ID', '1087363824973385617')  # Cập nhật sau khi lấy được
ZALO_WEBHOOK_SECRET = os.getenv('ZALO_WEBHOOK_SECRET', 'my-zalo-secret')  # Khóa bí mật cho webhook Zalo

# Base URL cho Zalo Bot API
ZALO_BASE_URL = 'https://bot-api.zapps.me'

# Hàm verify signature từ Facebook
def verify_signature(payload, signature):
    expected_sig = hmac.new(FB_APP_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return expected_sig == signature.split('=')[1]

# Hàm gửi thông báo qua Zalo Bot API
def send_zalo_notification(message_text):
    try:
        url = f"{ZALO_BASE_URL}/bot{ZALO_BOT_TOKEN}/sendMessage"
        zalo_msg = f"Có tin nhắn mới từ khách trên Facebook: {message_text}"
        payload = {
            "chat_id": ZALO_CHAT_ID,
            "text": zalo_msg
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            resp_json = response.json()
            if resp_json.get('ok', False):
                print(f"Zalo sent successfully: {resp_json.get('result', {})}")
                return True
            else:
                print(f"Zalo API error: {resp_json.get('description', 'Unknown error')}")
                return False
        else:
            print(f"HTTP error sending to Zalo: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Exception sending to Zalo: {e}")
        return False

# Route webhook Facebook (giữ nguyên)
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get('hub.verify_token') == FB_VERIFY_TOKEN:
            return request.args.get('hub.challenge')
        return "Invalid token", 403
    
    if request.method == 'POST':
        signature = request.headers.get('X-Hub-Signature-256')
        payload = request.data
        if not verify_signature(payload, signature):
            return "Invalid signature", 403
        
        data = json.loads(payload)
        if 'entry' in data:
            for entry in data['entry']:
                if 'messaging' in entry:
                    for msg in entry['messaging']:
                        sender_id = msg['sender']['id']
                        message_text = msg.get('message', {}).get('text', 'No text')
                        
                        # Gửi thông báo đến Zalo
                        send_zalo_notification(message_text)
        
        return Response(status=200)

# Route webhook Zalo (mới, để lấy chat_id)
@app.route('/zalo-webhook', methods=['POST'])
def zalo_webhook():
    secret_token = request.headers.get('X-Bot-Api-Secret-Token')
    if secret_token != ZALO_WEBHOOK_SECRET:
        print(f"Invalid Zalo webhook secret: {secret_token}")
        return Response(json.dumps({"message": "Unauthorized"}), status=403, mimetype='application/json')
    
    data = request.json
    print(f"Zalo webhook data: {json.dumps(data, indent=2)}")  # In toàn bộ dữ liệu để debug
    if data.get('ok', False) and 'result' in data:
        result = data['result']
        if 'message' in result and 'chat' in result['message']:
            chat_id = result['message']['chat']['id']
            print(f"Found chat_id: {chat_id}")
            # Gửi tin nhắn test để xác nhận
            send_zalo_notification(f"Test webhook Zalo, chat_id: {chat_id}")
    
    return Response(json.dumps({"message": "Success"}), status=200, mimetype='application/json')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
