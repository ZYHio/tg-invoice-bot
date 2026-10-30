from http.server import BaseHTTPRequestHandler
import json
import requests

TELEGRAM_BOT_TOKEN = "9124318135:AAEX-aaOW7oB4opdIzoWlF9bwqcg4w1v9N8"

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Error: {e}")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            if "message" in data:
                message = data["message"]
                chat_id = message["chat"]["id"]

                if "text" in message:
                    user_text = message["text"]
                    if user_text.startswith("/start"):
                        send_telegram_message(chat_id, "👋 欢迎使用记账机器人！直接发送消费文字（如：`午餐 15美金`）。")
                    else:
                        send_telegram_message(chat_id, f"✅ **已收到并记录**\n\n`{user_text}`")

            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"OK")
        except Exception as e:
            print(f"Error handling POST: {e}")
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"OK")