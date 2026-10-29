import os
import json
import base64
import requests
from http.server import BaseHTTPRequestHandler

# 从环境变量中读取密钥
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
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

            # 响应 Telegram 200 OK，告诉它消息已收到
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
            
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

    def parse_invoice_with_ai(self, image_url):
        # 组装 OpenAI Vision 提示词
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
        # 清理可能存在的 markdown 标签
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