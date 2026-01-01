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

# 載入環境變數
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = os.getenv("OPENROUTER_MODEL")
LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
GROUP_ID = os.getenv("LINE_TEST_GROUP_ID")

PUSH_MSG = False

# 取得輸入參數（年份、月份）
if len(sys.argv) not in [3, 4]:
    print("❌ 使用方式: python summarize_bible_progress.py <年份> <月份> [結束月份]")
    print("例如: python summarize_bible_progress.py 2025 7 (單月)")
    print("例如: python summarize_bible_progress.py 2025 7 8 (多月，包含7月和8月)")
    sys.exit(1)

try:
    target_year = int(sys.argv[1])
    start_month = int(sys.argv[2])
    end_month = int(sys.argv[3]) if len(sys.argv) == 4 else start_month
    assert 1 <= start_month <= 12 and 1 <= end_month <= 12 and start_month <= end_month
except:
    print("❌ 請輸入有效的年份和月份，例如：2025 6 或 2025 7 8")
    sys.exit(1)

# 初始化 LINE Bot
line_bot_api = LineBotApi(LINE_TOKEN)

# 根據 push_message.py 的固定名單，建立基礎資料結構
# 這樣才能知道誰沒有回報
all_members = ["心龢", "子新", "思凱", "燕和", "葉蓉", "育瑄", "淙富", "雅琪", "聖凱", "江衡", "昀峰"]
all_progress_by_person = {member: [] for member in all_members}


# 讀取並處理 msg_log.csv
with open("msg_log.csv", "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for row in reader:
        try:
            if "timestamp" not in row or "message" not in row:
                continue

            ts = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S")

            if ts.year == target_year and start_month <= ts.month <= end_month and "全年讀經進度回報" in row["message"]:
                text = row["message"]

                if "請大家填寫：" in text:
                    text_after_prompt = text.split("請大家填寫：", 1)[1]
                    lines = text_after_prompt.split('\\n')

                    for line in lines:
                        line = line.strip().replace('\n', '')
                        if not line:
                            continue


                        match = re.match(r'''^([\u4e00-\u9fa5]{2,4})：(.*)''', line)

                        if match:
                            name = match.group(1).strip()
                            progress = match.group(2).strip()

                            if progress and name in all_progress_by_person:
                                new_record = {
                                    "timestamp": ts.strftime("%Y-%m-%d"),
                                    "進度": progress
                                }
                                # 檢查是否為重複紀錄
                                if new_record not in all_progress_by_person[name]:
                                    all_progress_by_person[name].append(new_record)
        except (ValueError, KeyError):
            continue

# 標記無回報的成員
for name, records in all_progress_by_person.items():
    if not records:
        all_progress_by_person[name] = [{"進度": "無回報"}]


if not any(records and records[0].get("進度") != "無回報" for records in all_progress_by_person.values()):
    print("⚠️ 找不到指定月份的讀經進度資料。")
    sys.exit(0)

# 轉換為 JSON 字串
raw_text = json.dumps(all_progress_by_person, ensure_ascii=False, indent=2)


print(raw_text)

input()

# 呼叫 OpenRouter API 進行總結
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

system_prompt = """

你是一位教會小組的行政助理，請根據下方提供的 JSON 格式的讀經進度紀錄，撰寫一份簡明的讀經進度報告，提供給小組長與牧者參考。

這份 JSON 資料彙整了每位組員在指定月份內的所有進度回報。資料的 `key` 是組員姓名，`value` 是一個陣列（array），包含了他們每一次回報的時間戳（`timestamp`）與進度內容（`進度`）。

請依照以下格式與內容撰寫報告：

🔺 1. 各組員的進度範圍摘要
請根據每位組員的所有回報，總結出他們目前讀經的進度範圍。
→ 每位組員請以「🔸」開頭，格式範例如下：
🔸 子新：耶利米書～約珥書 1；馬太福音～羅馬書 11

🔺 2. 各組員的回報情況
請根據回報的次數與時間，指出每位組員是否有持續回報（例如：穩定回報(1個月只少3次)、回報 O 次、不穩定、本月尚未回報）。
→ 仍請以「🔸」開頭搭配人名與描述。

🔺 3. 各組員的進展狀況
請根據多次回報的內容，判斷各組員是否有明顯進展（有／無）。
→ 以「🔸」開頭列出各組員狀況。

🔺 4. 尚未回報或多週未更新者
請根據 JSON 資料，列出在這個月份沒有任何回報紀錄的組員姓名。

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

"""


system_prompt_forall = """

你是一位教會小組的行政助理，請根據下方提供的 JSON 格式的讀經進度紀錄，撰寫一份簡明的讀經進度報告，提供給小組員參考。

這份 JSON 資料彙整了每位組員在指定月份內的所有進度回報。資料的 `key` 是組員姓名，`value` 是一個陣列（array），包含了他們每一次回報的時間戳（`timestamp`）與進度內容（`進度`）。

請依照以下格式與內容撰寫報告：

🔺 1. 各組員的進度範圍摘要
請根據每位組員的所有回報，總結出他們目前讀經的進度範圍。
→ 每位組員請以「🔸」開頭，格式範例如下：
🔸 子新：耶利米書～約珥書 1；馬太福音～羅馬書 11

🔺 2. 各組員的進展摘要
請根據每位組員的所有回報，總結出他們時間範圍內讀經的進展。
→ 每位組員請以「🔸」開頭，格式範例如下：
🔸 子新：舊約5章、新約7章

🔺 3. 整體觀察與建議
請總結觀察，例如：
- 鼓勵有穩定回報者繼續保持
- 提醒未回報者更新進度
- 鼓勵彼此代禱、分享亮光與心得

⚠️ 格式要求：
- 每段請用條列方式撰寫，避免冗長段落。
- 每個人名前請加「🔸」，每大項目前加「🔺」。
- 請使用自然語氣（像是群組內的訊息），不要使用粗體、標題格式。
- 回應請用繁體中文撰寫。

"""








payload = {
    "model": MODEL_NAME,
    "messages": [
        {
            "role": "system",
            "content": system_prompt_forall
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
report_name = f"{target_year}年{start_month}月" if start_month == end_month else f"{target_year}年{start_month}~{end_month}月"
report_path = os.path.join(report_dir, f"{report_name}小組讀經_{timestamp_str}.txt")

with open(report_path, "w", encoding="utf-8") as f:
    f.write(summary)

# 發送到 LINE 群組
if PUSH_MSG:
    line_bot_api.push_message(GROUP_ID, TextSendMessage(text=summary))
    print(f"✅ 已產生 {report_name} 報告並推播。儲存於：{report_path}")
else:
    print(f"✅ 已產生 {report_name} 報告。儲存於：{report_path}")


