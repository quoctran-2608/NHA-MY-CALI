import requests
import json
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# Lưu ý: Để bảo mật, bạn nên đặt các giá trị nhạy cảm như token vào biến môi trường trên Render.
# Ví dụ: Trên Render, vào Environment Variables, thêm ZALO_BOT_TOKEN, ZALO_CHAT_ID, ZALO_BASE_URL.
# Sau đó, sử dụng os.environ.get('ZALO_BOT_TOKEN') thay vì hardcode.
ZALO_BOT_TOKEN = os.environ.get('ZALO_BOT_TOKEN', '1087363824973385617:crKKlfdMIEFnfJmmnRhTdczBYkEmYmzDhCciTLeyglWuqKonGKchjaCiztxfZiZp')
ZALO_CHAT_ID = os.environ.get('ZALO_CHAT_ID', '1f7c0fca289ec1c0988f')
ZALO_BASE_URL = os.environ.get('ZALO_BASE_URL', 'https://bot-api.zapps.me')

def send_zalo_notification(message_text):
    try:
        url = f"{ZALO_BASE_URL}/bot{ZALO_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": ZALO_CHAT_ID,
            "text": message_text
        }
        headers = {
            "Content-Type": "application/json"
        }
        print(f"Sending Zalo API request: {url}, payload: {json.dumps(payload)}")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            resp_json = response.json()
            print(f"Zalo API response: {json.dumps(resp_json, indent=2)}")
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

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    
    message_text = data.get('text')
    if not message_text:
        return jsonify({"error": "No 'text' field provided in JSON"}), 400
    
    success = send_zalo_notification(message_text)
    if success:
        return jsonify({"status": "success", "message": "Notification sent to Zalo"}), 200
    else:
        return jsonify({"status": "error", "message": "Failed to send notification to Zalo"}), 500
   
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
