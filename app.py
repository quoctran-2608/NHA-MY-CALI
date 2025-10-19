import asyncio
from flask import Flask, request, Response
import requests
import hmac
import hashlib
import json
import os
from zalo_bot import Bot

app = Flask(__name__)

# Biến cấu hình (dùng env vars cho bảo mật)
FB_VERIFY_TOKEN = os.getenv('FB_VERIFY_TOKEN', 'mysecret')
FB_APP_SECRET = os.getenv('FB_APP_SECRET', 'your_facebook_app_secret')
ZALO_BOT_TOKEN = os.getenv('ZALO_BOT_TOKEN', '1087363824973385617:crKKlfdMIEFnfJmmnRhTdczBYkEmYmzDhCciTLeyglWuqKonGKchjaCiztxfZiZp')
ZALO_CHAT_ID = os.getenv('ZALO_CHAT_ID', '1087363824973385617')  # Thay bằng chat_id từ bước 1

# Tạo Zalo bot client
zalo_bot = Bot(ZALO_BOT_TOKEN)

# Hàm verify signature từ Facebook
def verify_signature(payload, signature):
    expected_sig = hmac.new(FB_APP_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return expected_sig == signature.split('=')[1]

# Hàm gửi thông báo qua Zalo bot
async def send_zalo_notification(message_text):
    try:
        async with zalo_bot:
            zalo_msg = f"Có tin nhắn mới từ khách trên Facebook: {message_text}"
            await zalo_bot.send_message(ZALO_CHAT_ID, zalo_msg)
        return True
    except Exception as e:
        print(f"Error sending to Zalo: {e}")
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
                        message_text = msg.get('message', {}).get('text', 'No text')
                        
                        # Chạy async để gửi Zalo
                        asyncio.run(send_zalo_notification(message_text))
        
        return Response(status=200)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)