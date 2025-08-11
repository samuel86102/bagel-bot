import csv
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import requests
from linebot import LineBotApi
from linebot.models import TextSendMessage
import json
import re


def extract_progress_to_json(text: str) -> str:
    # 找到「請大家填寫：」後的內容開始處理
    if "請大家填寫：" in text:
        text = text.split("請大家填寫：", 1)[1]
        text = text.replace('\\n', '\n')

    # 使用正則表達式擷取「姓名：進度（可為空）」的行
    matches = re.findall(r'^([\u4e00-\u9fa5]{2,4})：([^\n]*)', text, re.MULTILINE)

    # 轉成字典
    progress_dict = {name.strip(): progress.strip() for name, progress in matches}

    # 轉為 JSON 字串（保留中文）
    #return json.dumps(progress_dict, ensure_ascii=False, indent=2)
    print(progress_dict.keys())
    return json.dumps(progress_dict, ensure_ascii=False)

# 載入環境變數
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = os.getenv("OPENROUTER_MODEL")
LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
GROUP_ID = os.getenv("LINE_TEST_GROUP_ID")

# 取得輸入參數（年份、月份）
if len(sys.argv) != 3:
    print("❌ 使用方式: python summarize_bible_progress.py <年份> <月份>")
    sys.exit(1)

try:
    target_year = int(sys.argv[1])
    target_month = int(sys.argv[2])
    assert 1 <= target_month <= 12
except:
    print("❌ 請輸入有效的年份和月份，例如：2025 6")
    sys.exit(1)

# 初始化 LINE Bot
line_bot_api = LineBotApi(LINE_TOKEN)

# 過濾符合月份的讀經訊息
progress_messages = []
with open("msg_log.csv", "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for row in reader:
        try:
            ts = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S")
            if ts.year == target_year and ts.month == target_month and "全年讀經進度回報" in row["message"]:

                json_string = extract_progress_to_json(row["message"])


                #progress_messages.append(row["message"])
                progress_messages.append(json_string)
        except ValueError:
            continue

if not progress_messages:
    print("⚠️ 找不到指定月份的讀經進度資料。")
    sys.exit(0)

raw_text = "\n\n".join(progress_messages)

print(raw_text)
input()

# 呼叫 OpenRouter API 進行總結
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


system_prompt = """

你是一位教會小組的行政助理，請根據下方提供的讀經進度接龍紀錄，撰寫一份簡明的讀經進度報告，提供給小組長與牧者參考。

請依照以下格式與內容撰寫報告：

🔺 1. 各組員的進度範圍摘要  
請列出每位組員目前讀經的範圍。  
→ 每位組員請以「🔸」開頭，格式範例如下：  
🔸 子新：耶利米書～約珥書 1；馬太福音～羅馬書 11

🔺 2. 各組員的回報情況  
請指出每位組員是否有持續回報（有／不穩定／無）。  
→ 仍請以「🔸」開頭搭配人名與描述。

🔺 3. 各組員的進展狀況  
請判斷各組員是否有明顯進展（有／無），如有多次回報或從舊約跳到新約即算有進展。  
→ 以「🔸」開頭列出各組員狀況。

🔺 4. 尚未回報或多週未更新者  
請列出沒有任何回報，或已多週未更新的組員姓名。若可能，註明其上次狀況（如：「數週前有回報」、「從未回報」等）。

🔺 5. 共通進度觀察  
若觀察到多人在讀相同卷書或段落，請簡單統整描述。

🔺 6. 整體觀察與建議  
請總結觀察，例如：
- 鼓勵有穩定回報者繼續保持
- 提醒未回報者更新進度
- 鼓勵彼此代禱、分享亮光與心得

⚠️ 格式要求：
- 每段請用條列方式撰寫，避免冗長段落。
- 每個人名前請加「🔸」，每大項目前加「🔺」。
- 請使用自然語氣（像是群組內的訊息），不要使用粗體、標題格式。
- 回應請用繁體中文撰寫。

📌 備註：每筆資料是組員在群組的接龍紀錄，不代表每週固定進度。請根據實際紀錄判斷其讀經情形。

"""



'''
system_prompt = """

你是一位教會小組的行政助理，請根據以下的讀經進度回報訊息，為小組長與牧者撰寫一份簡明的報告。
每一筆資料代表每個人在群組裡面的接龍，不代表每週的進度

請包含以下幾項內容：

1. 條列每一位組員的讀經進度摘要，包括：進度範圍、是否有持續回報、是否有明顯進展。用「🔺」作為list的開頭
2. 指出哪些人尚未回報，或已多週未更新。
3. 若有共通性（如多人同時在讀某卷書），可簡單統整。
4. 針對整體狀況給出簡短的觀察與建議，例如鼓勵穩定者、提醒未更新者等。

請使用清楚的條列格式，以幫助牧者與小組長快速掌握整體屬靈狀況。
人名list 開頭用「🔸」符號
請使用繁體中文回答。
不要使用bold text，當成一般傳在群組裡的純文字訊息


"""
'''


payload = {
    "model": MODEL_NAME,
    "messages": [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": raw_text
        }
    ]
}

response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
result = response.json()
summary = result["choices"][0]["message"]["content"]

# 儲存報告檔案
timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
report_dir = "report"
os.makedirs(report_dir, exist_ok=True)
report_path = os.path.join(report_dir, f"{target_year}年{target_month}月小組讀經_{timestamp_str}.txt")

with open(report_path, "w", encoding="utf-8") as f:
    f.write(summary)

# 發送到 LINE 群組
line_bot_api.push_message(GROUP_ID, TextSendMessage(text=summary))

print(f"✅ 已產生 {target_year} 年 {target_month} 月報告並推播。儲存於：{report_path}")

