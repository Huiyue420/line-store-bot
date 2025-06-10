from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv
import os
import json
import logging
from logging import Formatter
from pythonjsonlogger import jsonlogger

from utils.command_handler import handle_command
from utils.user_state import UserState
from utils.auth import is_admin

# 載入環境變數
load_dotenv()

app = Flask(__name__)

# LINE Bot 設定
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# 設定日誌
logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# 確保資料目錄存在
os.makedirs('data', exist_ok=True)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    
    # 記錄收到的訊息
    logger.info('收到訊息', extra={
        'user_id': user_id,
        'user_message': text
    })
    
    try:
        # 處理命令並取得回應
        response = handle_command(text, user_id)
        
        # 發送回應
        if response:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=response)
            )
    
    except Exception as e:
        logger.error('處理訊息時發生錯誤', extra={
            'error': str(e),
            'user_id': user_id,
            'user_message': text
        })
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="抱歉，處理您的請求時發生錯誤。請稍後再試。")
        )

if __name__ == "__main__":
    app.run(debug=os.getenv('DEBUG', 'False').lower() == 'true') 