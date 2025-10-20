from flask import Flask, request, Response
import hmac
import hashlib
import json
import os
import requests

app = Flask(__name__)

# Biến cấu hình (dùng env vars cho bảo mật)
FB_VERIFY_TOKEN = os.getenv('FB_VERIFY_TOKEN', 'mysecret')
FB_APP_SECRET = os.getenv('FB_APP_SECRET', '9ea198059a894a995edd4ef9e57b6b00')
FB_PAGE_ACCESS_TOKEN = os.getenv('FB_PAGE_ACCESS_TOKEN', 'your_page_access_token_here')  # Thêm access token cho Page để lấy thông tin user
ZALO_BOT_TOKEN = os.getenv('ZALO_BOT_TOKEN', '1087363824973385617:crKKlfdMIEFnfJmmnRhTdczBYkEmYmzDhCciTLeyglWuqKonGKchjaCiztxfZiZp')
ZALO_CHAT_ID = os.getenv('ZALO_CHAT_ID', '1f7c0fca289ec1c0988f')
ZALO_BASE_URL = 'https://bot-api.zapps.me'

# Hàm verify signature từ Facebook
def verify_signature(payload, signature):
    expected_sig = hmac.new(FB_APP_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return expected_sig == signature.split('=')[1]

# Hàm lấy tên user từ Facebook Graph API
def get_facebook_user_name(sender_id):
    try:
        url = f"https://graph.facebook.com/v20.0/{sender_id}?fields=name&access_token={FB_PAGE_ACCESS_TOKEN}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get('name', 'Khách hàng không xác định')
        else:
            print(f"Error fetching Facebook user name: {response.status_code} - {response.text}")
            return 'Khách hàng không xác định'
    except Exception as e:
        print(f"Exception fetching Facebook user name: {e}")
        return 'Khách hàng không xác định'

# Hàm gửi thông báo đến Zalo
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

# Route webhook Facebook
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
                        message_text = msg.get('message', {}).get('text', 'Không có nội dung văn bản')
                        user_name = get_facebook_user_name(sender_id)
                        full_message = f"Có tin nhắn mới từ {user_name} trên Facebook Messenger: {message_text}"
                        print(full_message)
                        send_zalo_notification(full_message)
        
        return Response(status=200)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
