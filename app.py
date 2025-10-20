from flask import Flask, request, Response
import hmac
import hashlib
import json
import os

app = Flask(__name__)

# Biến cấu hình (dùng env vars cho bảo mật)
FB_VERIFY_TOKEN = os.getenv('FB_VERIFY_TOKEN', 'mysecret')
FB_APP_SECRET = os.getenv('FB_APP_SECRET', '9ea198059a894a995edd4ef9e57b6b00')

# Hàm verify signature từ Facebook
def verify_signature(payload, signature):
    expected_sig = hmac.new(FB_APP_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return expected_sig == signature.split('=')[1]

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
                        print(f"New message from {sender_id}: {message_text}")
        
        return Response(status=200)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
