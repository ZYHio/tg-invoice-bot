from http.server import BaseHTTPRequestHandler
import json
import os
import requests

# 固定的 Telegram Bot Token
TELEGRAM_BOT_TOKEN = "9124318135:AAEX-aaOW7oB4opdIzoWlF9bwqcg4w1v9N8"

def send_telegram_message(chat_id, text):
    """向 Telegram 用户发送文本消息"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Error sending message: {e}")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """处理 Vercel 健康检查"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(b"FTL Invoice Bot is running (Simple Mode).")

    def do_POST(self):
        """处理 Telegram Webhook 消息"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            # 提取消息
            if "message" in data:
                message = data["message"]
                chat_id = message["chat"]["id"]

                # 1. 收到文本
                if "text" in message:
                    user_text = message["text"]
                    if user_text.startswith("/start"):
                        send_telegram_message(chat_id, "👋 欢迎使用极简记账机器人！直接发送消费文字（例如：`午餐 15美金`），我将直接为您记录。")
                    else:
                        # 极简模式：直接回显确认收到
                        reply = f"✅ **已收到并记录**\n\n`{user_text}`"
                        send_telegram_message(chat_id, reply)

                # 2. 收到图片
                elif "photo" in message:
                    send_telegram_message(chat_id, "📸 图片已收到！当前为极简模式，请直接发文字记账哦。")

            # 统一返回 200，防止 Telegram 重复投递
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