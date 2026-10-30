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
        """当你在浏览器直接打开网址首页时，展示好看的控制台内容"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html = """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <title>FTL Telegram Bot 控制台</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                .card { background: #1e293b; padding: 40px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); text-align: center; max-width: 450px; width: 100%; border: 1px solid #334155; }
                h0 { font-size: 24px; margin-bottom: 10px; color: #38bdf8; }
                .status { display: inline-block; padding: 6px 12px; background: #065f46; color: #34d399; border-radius: 20px; font-size: 14px; font-weight: bold; margin-bottom: 20px; }
                p { color: #94a3b8; font-size: 14px; line-height: 1.6; }
                .btn { display: inline-block; margin-top: 20px; padding: 10px 20px; background: #0284c7; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; transition: background 0.2s; }
                .btn:hover { background: #0369a1; }
            </style>
        </head>
        <body>
            <div class="card">
                <h2>🚀 FTL Telegram Bot</h2>
                <div class="status">● 运行中 (Online)</div>
                <p>当前服务运行于 Vercel 无服务器环境。<br>Webhook 通道已就绪，随时准备接收你的记账消息。</p>
                <a class="btn" href="https://t.me/你的机器人用户名" target="_blank">前往 Telegram 聊天</a>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode('utf-8'))

    def do_POST(self):
        """处理 Telegram Webhook 消息"""
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
                        send_telegram_message(chat_id, "👋 欢迎使用专属记账机器人！直接发送消费文字（例如：`午餐 15美金`），我将直接为您记录。")
                    else:
                        reply = f"✅ **已收到并记录**\n\n`{user_text}`"
                        send_telegram_message(chat_id, reply)

                elif "photo" in message:
                    send_telegram_message(chat_id, "📸 图片已收到！")

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