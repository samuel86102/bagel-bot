import os
import requests
from dotenv import load_dotenv
from datetime import datetime
print("現在時間：", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


# 讀取環境變數
load_dotenv()

LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
#GROUP_ID = os.getenv("LINE_TEST_GROUP_ID")
GROUP_ID = os.getenv("LINE_GROUP_ID")

def push_text_message(text):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "to": GROUP_ID,
        "messages": [
            {
                "type": "text",
                "text": text
            }
        ]
    }

    response = requests.post(url, json=body, headers=headers)
    print(f"Status: {response.status_code}, Response: {response.text}")

if __name__ == "__main__":


    text_msg = """【每週一 全年讀經進度接龍回報】

像一棵樹栽在溪水旁，按時候結果子，葉子也不枯乾。凡他所做的盡都順利。詩篇1：3

2025年是我們的「裝備與栽植年」，年度目標是「建立榮耀上帝的情誼，栽植在溪水旁的換新」🌟
為了能夠培養對信耶穌的堅信、能明白耶穌的心、跟隨愛慕神旨意而活，我們需要每天分別時間來讀神的話語。每週一是我們的全年讀經進度回報日，請大家填寫：

心龢：
子新：
思凱：
燕和：
葉蓉：
育瑄：
淙富：
雅琪：
聖凱：
江衡：
昀峰："""


    push_text_message(text_msg)
    #push_text_message("大家記得讀經喔！")

