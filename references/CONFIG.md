# 設定檔案說明

## config.json 完整欄位

```json
{
  "location": "Taipei,Taiwan",
  "topics": [
    ["分類名稱", "搜尋關鍵字"]
  ],
  "news_count": 2,
  "voice_max_duration": 300,
  "sources": ["gnews", "newsdata"],
  "gnews_api_key": "YOUR_GNEWS_API_KEY",
  "newsdata_api_key": "YOUR_NEWSDATA_API_KEY",
  "telegram_bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
  "telegram_chat_id": "YOUR_TELEGRAM_CHAT_ID"
}
```

## 欄位說明

### location
天氣查詢地點。

| 格式 | 範例 |
|------|------|
| 城市 | `"Taipei"` |
| 城市,國家 | `"Taipei,Taiwan"` |
| 中文 | `"新店"` |

### topics
二維陣列，`[分類名稱, 搜尋關鍵字]`。

最多 10 則新聞，會隨機混合各分類。

### news_count
每個分類抓取的新聞數量。

預設：`2`
建議：`1-3`（太多會讓語音過長）

### voice_max_duration
語音最大時長（秒）。

預設：`300`（5 分鐘）

### sources
使用的新聞來源。

| 值 | 說明 |
|----|------|
| `["gnews"]` | 只用 GNews |
| `["newsdata"]` | 只用 NewsData |
| `["gnews", "newsdata"]` | 同時使用，GNews 為主 |

## API Key 申請

### GNews API
1. 前往 https://gnews.io/register
2. 免費額度：100次/天，12小時延遲
3. 複製 API Key

### NewsData.io
1. 前往 https://newsdata.io/register
2. 免費額度：500次/天
3. 複製 API Key（格式：`pub_xxxxx`）

### Telegram Bot
1. @BotFather 傳送 `/newbot`
2. 取得 Bot Token
3. 取得 Chat ID（傳訊息給 @userinfobot）

### OpenAI API
放在 `~/.openclaw/openclaw.json`：

```json
{
  "models": {
    "providers": {
      "openai": {
        "apiKey": "YOUR_OPENAI_API_KEY"
      }
    }
  }
}
```

## Cron 排程建議

### 每日晨報（推薦）
```bash
30 7 * * * cd /home/ubuntu && python3 PATH/TO/daily_podcast.py
```

### 測試模式（手動執行）
```bash
python3 ~/clawd/skills/daily-podcast/scripts/daily_podcast.py
```

### 查看執行日誌
```bash
tail -f ~/clawd/podcast/daily.log
```

## 輸出檔案位置

| 類型 | 路徑 |
|------|------|
| 初稿 | `~/clawd/podcast/draft_YYYYMMDD.txt` |
| 潤飾稿 | `~/clawd/podcast/script_YYYYMMDD.txt` |
| 語音 | `~/.openclaw/media/daily_YYYYMMDD.mp3` |
| 標題存档 | `~/clawd/memory/daily-podcast-YYYY-MM-DD.md` |

## Agent 回報格式

當用戶問「今天晨報涵蓋了哪些項目」時，Agent 應讀取 `memory/daily-podcast-YYYY-MM-DD.md` 並回報：

```
今天的晨報摘要包含以下項目：

【國際】
- [標題1]（來源：xxx）
- [標題2]（來源：xxx）

【經濟】
- [標題1]（來源：xxx）
...

如需深入了解任何項目，請告訴我！
```

## 關於 Token 消耗

此技能設計為「隔離任務」：

| 特性 | 說明 |
|------|------|
| 執行方式 | Cron Job 獨立執行，不占用對話上下文 |
| Token 消耗 | 僅消耗 AI 潤飾的 API token |
| 對話影響 | 無，不會讓主對話變長 |

這是專為「定期任務」設計的架構，適合每天執行的晨報、備份、監控等場景。

## 故障排除

| 問題 | 解法 |
|------|------|
| 語音太長 | 減少 `news_count` 或 `topics` 數量 |
| 無法發送 Telegram | 檢查 `telegram_bot_token` 和 `telegram_chat_id` |
| 新聞重複 | 只使用其中一個 `sources` |
