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
ZALO_BOT_TOKEN = os.getenv('ZALO_BOT_TOKEN', '1087363824973385617:crKKlfdMIEFnfJmmnRhTdczBYkEmYmzDhCciTLeyglWuqKonGKchjaCiztxfZiZp')
ZALO_CHAT_ID = os.getenv('ZALO_CHAT_ID', '1f7c0fca289ec1c0988f')
ZALO_BASE_URL = 'https://bot-api.zapps.me'

# Hàm verify signature từ Facebook
def verify_signature(payload, signature):
    expected_sig = hmac.new(FB_APP_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return expected_sig == signature.split('=')[1]

# Hàm gửi thông báo đến Zalo
def send_zalo_notification(message_text):
    try:
        url = f"{ZALO_BASE_URL}/bot/{ZALO_BOT_TOKEN}/sendMessage"  # Thêm '/' sau 'bot' nếu cần, nhưng theo docs là không
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

# Hàm mới: Lấy updates từ Zalo để xác thực chat_id
def get_zalo_updates():
    try:
        url = f"{ZALO_BASE_URL}/bot/{ZALO_BOT_TOKEN}/getUpdates"
        payload = {}  # Có thể thêm params như offset, limit nếu cần (tương tự Telegram)
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            resp_json = response.json()
            print(f"Zalo getUpdates response: {json.dumps(resp_json, indent=2)}")
            if resp_json.get('ok', False):
                updates = resp_json.get('result', [])
                chat_ids = []
                for update in updates:
                    if 'message' in update:
                        chat_id = update['message'].get('chat', {}).get('id')
                        if chat_id:
                            chat_ids.append(chat_id)
                            print(f"Found chat_id: {chat_id} from user: {update['message'].get('from', {}).get('id')}")
                if chat_ids:
                    print(f"Available chat_ids: {chat_ids}. Hãy dùng một trong số này cho ZALO_CHAT_ID.")
                else:
                    print("No updates found. Hãy gửi tin nhắn cho bot trước.")
                return chat_ids
            else:
                print(f"getUpdates error: {resp_json.get('description')}")
                return None
        else:
            print(f"HTTP error in getUpdates: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception in getUpdates: {e}")
        return None

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
                        message_text = msg.get('message', {}).get('text', 'No text')
                        full_message = f"New message from {sender_id}: {message_text}"
                        print(full_message)
                        send_zalo_notification(full_message)
        
        return Response(status=200)

# Route mới để test getUpdates (truy cập localhost:10000/test_updates)
@app.route('/test_updates', methods=['GET'])
def test_updates():
    chat_ids = get_zalo_updates()
    if chat_ids:
        return f"Chat IDs found: {chat_ids}", 200
    else:
        return "No chat IDs found or error occurred. Check console logs.", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
