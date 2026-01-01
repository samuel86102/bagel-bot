# 🍩 貝果小幫手 (Bagel Bot)

>幫助教會小組追蹤和提醒成員的每日讀經進度的 LINE Bot 🎉

## 核心功能

*   **每週提醒**：自動發送一個固定的LINE訊息，提醒小組成員回報他們的讀經進度。
*   **訊息紀錄**：作為一個 Webhook 伺服器，可持續監聽 LINE 群組中的所有訊息，並將其記錄下來以供後續分析。
*   **進度總結與報告**：能夠分析紀錄的訊息，篩選出指定月份的讀經進度回報，並使用 AI（OpenRouter）產生一份詳細的進度報告。

## 系統組件

本系統由以下三個核心 Python 腳本組成：

### 1. `push_message.py`

*   **功能**：負責向指定的 LINE 群組發送一個固定的提醒訊息。訊息內容是預設的，主要用於每週一提醒大家回報讀經進度。
*   **用途**：當您想手動或透過排程（例如 crontab）發送提醒時執行此腳本。
*   **第一次執行**：若要獲取群組 ID (`group_id`)，您可以先執行 `webhook_server.py`，在群組中發送任何訊息後，`group_id` 就會顯示在伺服器的終端機輸出中。

### 2. `webhook_server.py`

*   **功能**：這是一個基於 Flask 的 Web 伺服器，它會接收來自 LINE 的 Webhook 事件。當群組中有任何文字訊息時，它會將訊息的詳細資訊（時間、使用者ID、群組ID、訊息內容）記錄到 `msg_log.csv` 檔案中。
*   **用途**：需要常駐執行，以確保所有群組對話都能被記錄下來。如果您只需要做定期的進度分析，也可以只在需要收集數據的時段執行。
*   **注意**：此伺服器有一個 `is_reply` 變數，預設為 `False`。如果設為 `True`，它會自動回覆收到的每一則訊息。

### 3. `summarize_bible_progress.py`

*   **功能**：這是系統的核心分析工具。它會讀取 `msg_log.csv` 的紀錄，並根據使用者輸入的年份和月份，篩選出與讀經進度相關的回報。
*   **處理流程**：
    1.  解析日誌，根據固定的成員名單（`all_members`）整理每位成員的回報。
    2.  將整理後的數據（JSON 格式）發送到 OpenRouter API，使用一個預設的 prompt 來產生一份有結構的摘要報告。
    3.  報告會儲存到 `report/` 資料夾下的一個 `.txt` 檔案。
    4.  可以選擇性地（透過 `PUSH_MSG` 變數）將產生的報告直接發送到 LINE 群組。

## 安裝與設定

1.  **安裝依賴**：
    ```bash
    pip install -r requirements.txt
    ```
    *(註：專案中尚未包含 `requirements.txt`，您需要根據 `import` 的套件手動建立，主要包含 `requests`, `python-dotenv`, `Flask`, `line-bot-sdk`, `pandas`)*

2.  **設定環境變數**：
    在專案根目錄下建立一個名為 `.env` 的檔案，並填入以下內容：
    ```
    # LINE Bot 的設定
    LINE_ACCESS_TOKEN="YOUR_LINE_CHANNEL_ACCESS_TOKEN"
    LINE_SECRET="YOUR_LINE_CHANNEL_SECRET"
    LINE_GROUP_ID="YOUR_TARGET_LINE_GROUP_ID"
    LINE_TEST_GROUP_ID="YOUR_TEST_LINE_GROUP_ID" # 可選，用於測試

    # OpenRouter API 的設定
    OPENROUTER_API_KEY="YOUR_OPENROUTER_API_KEY"
    OPENROUTER_MODEL="YOUR_AI_MODEL_NAME" # 例如: google/gemini-pro
    ```

## 使用方式

### 啟動訊息監聽服務

若要開始記錄群組訊息，請執行 `webhook_server.py`。您需要一個可公開存取的網址（例如使用 `ngrok`）來接收 LINE 的 Webhook。

```bash
python webhook_server.py
```
*伺服器將會運行在 `http://0.0.0.0:5003`。*

### 手動發送提醒

若要發送每週的讀經進度提醒，請執行：

```bash
python push_message.py
```

### 產生讀經進度報告

若要分析特定月份的讀經進度並產生報告，請執行 `summarize_bible_progress.py`，並帶上年份和月份作為參數。

*   **分析單一月份** (例如 2025 年 7 月):
    ```bash
    python summarize_bible_progress.py 2025 7
    ```

*   **分析多個月份** (例如 2025 年 7 月到 8 月):
    ```bash
    python summarize_bible_progress.py 2025 7 8
    ```

報告將會儲存在 `report/` 資料夾中。

## 檔案說明

*   `.gitignore`: Git 的忽略設定檔。
*   `msg_log.csv`: 由 `webhook_server.py` 產生的訊息日誌檔案。
*   `report/`: 由 `summarize_bible_progress.py` 產生的所有報告都會存放在這裡。
