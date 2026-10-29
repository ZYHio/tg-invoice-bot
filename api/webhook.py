import os
import json
import requests
from http.server import BaseHTTPRequestHandler

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 浏览器直接访问时，返回一个优雅的 Hello 状态欢迎页
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>FTL Invoice Bot</title>
            <style>
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
                    display: flex; justify-content: center; align-items: center; 
                    height: 100vh; margin: 0; background: #0f172a; color: #f8fafc; 
                }
                .card { 
                    text-align: center; padding: 40px; background: #1e293b; 
                    border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); 
                    max-width: 400px; width: 100%;
                }
                h1 { color: #38bdf8; margin-bottom: 10px; font-size: 24px; }
                p { color: #94a3b8; font-size: 14px; line-height: 1.5; }
                .status { display: inline-block; margin-top: 15px; padding: 6px 12px; background: #065f46; color: #34d399; border-radius: 20px; font-size: 12px; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>👋 Hello! FTL Invoice Bot</h1>
                <p>Telegram Webhook backend is online and running successfully on Vercel.</p>
                <div class="status">● System Operational</div>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html_content.encode('utf-8'))

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            update = json.loads(post_data.decode('utf-8'))
            
            # 处理用户发来的图片
            if "message" in update and "photo" in update["message"]:
                message = update["message"]
                chat_id = message["chat"]["id"]
                
                # 获取最高清的图片 file_id
                file_id = message["photo"][-1]["file_id"]
                
                # 1. 向 Telegram 获取图片下载链接
                file_info_res = requests.get(f"{TELEGRAM_API_URL}/getFile?file_id={file_id}").json()
                file_path = file_info_res["result"]["file_path"]
                image_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
                
                # 2. 调用大模型视觉解析发票
                invoice_data = self.parse_invoice_with_ai(image_url)
                
                # 3. 发送带确认按钮的互动卡片给用户
                self.send_confirmation_message(chat_id, invoice_data)

            # 响应 Telegram 200 OK
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
            
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

    def parse_invoice_with_ai(self, image_url):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "请提取这张发票的 JSON 数据：{\"date\": \"YYYY-MM-DD\", \"vendor\": \"商家\", \"amount\": 0.00, \"category\": \"分类\"}。只返回纯JSON。"},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            "max_tokens": 300
        }
        res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        result_text = res.json()["choices"][0]["message"]["content"].strip()
        result_text = result_text.replace("```json", "").replace("```", "").strip()
        return json.loads(result_text)

    def send_confirmation_message(self, chat_id, data):
        text = (
            f"📄 **识别到发票**：\n"
            f"📅 日期: {data.get('date')}\n"
            f"🏪 商家: {data.get('vendor')}\n"
            f"💰 金额: `¥{data.get('amount')}`\n\n"
            f"请确认金额是否正确？"
        )
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ 确认无误并写入", "callback_data": f"save_{data.get('amount')}"},
                    {"text": "❌ 取消", "callback_data": "cancel"}
                ]
            ]
        }
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "reply_markup": json.dumps(keyboard)
        }
        requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)