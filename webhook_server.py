from flask import Flask, request, abort
from dotenv import load_dotenv
import os
from datetime import datetime
import pandas as pd


# LINE SDK v3 匯入
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient, TextMessage, ReplyMessageRequest
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.exceptions import InvalidSignatureError



# 讀取環境變數
load_dotenv()

channel_secret = os.getenv("LINE_SECRET")
channel_access_token = os.getenv("LINE_ACCESS_TOKEN")



is_reply = False



app = Flask(__name__)

# 建立 Messaging API 實例
configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    if event.source.type == 'group':
        group_id = event.source.group_id
        print(f"收到來自群組的訊息, groupID：{group_id}")
    else:
        group_id = ""

    user_id = event.source.user_id
    print(f"收到來自使用者的訊息, userID: {user_id}:")
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    print(f"Timestamp: {timestamp}")

    # === msg log ===
    # 使用者傳的文字訊息
    message_text = event.message.text.replace('\n', '\\n')


    # 建立一筆 log
    df_msg_log = pd.DataFrame([{
        "timestamp": timestamp,
        "group_id": group_id,
        "user_id": user_id,
        "message": message_text
    }])

    # 儲存路徑
    csv_file = "msg_log.csv"

    # 是否已存在檔案
    file_exists = os.path.isfile(csv_file)

    # Append 寫入 CSV
    df_msg_log.to_csv(csv_file, mode='a', header=not file_exists, index=False)

    # Debug print
    print("訊息已記錄到 msg_log.csv")
    print(df_msg_log)

    if is_reply:
        with ApiClient(configuration) as api_client:
            messaging_api = MessagingApi(api_client)
            reply_message = ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=f"你說的是：{event.message.text}")]
            )
            messaging_api.reply_message(reply_message)





if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5003)

