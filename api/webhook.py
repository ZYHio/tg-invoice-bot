from http.server import BaseHTTPRequestHandler
import json
import os
import requests
from openai import OpenAI

# 从环境变量获取 Token 和 Key
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "9124318135:AAEX-aaOW7oB4opdIzoWlF9bwqcg4w1v9N8")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

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

def parse_text_with_gpt(text):
    """使用 GPT-4o 解析记账文字"""
    if not OPENAI_API_KEY:
        return "⚠️ OpenAI API Key 未配置，无法解析文本。"

    client = OpenAI(api_key=OPENAI_API_KEY)
    
    prompt = f"""
    你是一个财务记账助手。请从用户的文字中提取发票/消费信息，并格式化输出：
    1. 商家名称
    2. 交易日期 (如 YYYY-MM-DD，若未提及则填“今日”)
    3. 总金额 (含币种，如 $50.00)
    4. 消费类别 (如 餐饮、办公用品、交通等)

    用户输入："{text}"
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ GPT 解析失败: {str(e)}"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """处理 Vercel 健康检查"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>FTL Invoice Bot Status</title></head>
        <body style="font-family: sans-serif; text-align: center; padding: 50px; background: #0f172a; color: white;">
            <h1>👋 Hello! FTL Invoice Bot is Running</h1>
            <p>Status: <span style="color: #22c55e;">● Operational</span></p>
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

            # 提取消息信息
            if "message" in data:
                message = data["message"]
                chat_id = message["chat"]["id"]

                # 1. 如果发送的是文字
                if "text" in message:
                    user_text = message["text"]
                    # 排除 /start 指令
                    if user_text.startswith("/start"):
                        send_telegram_message(chat_id, "👋 欢迎使用记账机器人！直接发消费文字给我即可（例如：`今天午餐花费 $15.5`）。")
                    else:
                        send_telegram_message(chat_id, "⏳ 正在使用 GPT-4o 解析记账信息...")
                        ai_result = parse_text_with_gpt(user_text)
                        send_telegram_message(chat_id, ai_result)

                # 2. 如果发送的是图片，提示暂不支持
                elif "photo" in message:
                    send_telegram_message(chat_id, "📸 收到图片！当前已切换为文字记账模式，请直接发送消费文字（如：`打车 $25`）给机器人哦。")

            # 始终返回 200，防止 Telegram 重新投递
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"OK")

        except Exception as e:
            print(f"Error handling POST: {e}")
            self.send_response(200)  # 即使出错也给 Telegram 200，防止 500 死循环
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"OK")