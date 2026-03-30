# 設定檔案說明

## config.json 完整欄位

```json
{
  "location": "Taipei,Taiwan",
  "listener_name": "朋友",
  "topics": [
    ["分類名稱", "搜尋關鍵字"]
  ],
  "news_count": 2,
  "voice_max_duration": 300,
  "sources": ["gnews", "newsdata"],
  "pipeline_mode": "agent_delegated",
  "llm_provider": "openai-compatible",
  "llm_base_url": "https://api.openai.com/v1/chat/completions",
  "llm_model": "gpt-4o-mini",
  "llm_api_key": "YOUR_LLM_API_KEY",
  "gnews_api_key": "YOUR_GNEWS_API_KEY",
  "newsdata_api_key": "YOUR_NEWSDATA_API_KEY",
  "telegram_bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
  "telegram_chat_id": "YOUR_TELEGRAM_CHAT_ID"
}
```

## 欄位說明

### listener_name
晨報開場稱呼（避免固定寫死某個名字）。

建議第一次安裝時由 Agent 主動詢問使用者偏好稱呼，再寫入此欄位。

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

### pipeline_mode
內容流程模式。

| 值 | 說明 |
|----|------|
| `agent_delegated` | 只做資料彙整與初稿，翻譯/潤飾交給使用者 Agent |
| `self_render` | 由本 skill 直接完成翻譯與潤飾 |

> 建議預設使用 `agent_delegated`，可讓客戶用自己的模型與語氣。

### sources
使用的新聞來源。

| 值 | 說明 |
|----|------|
| `["gnews"]` | 只用 GNews |
| `["newsdata"]` | 只用 NewsData |
| `["gnews", "newsdata"]` | 同時使用，GNews 為主 |

### llm_provider / llm_base_url / llm_model / llm_api_key
翻譯與潤飾所用的模型設定（支援客戶自有模型）。

- `llm_provider`: 僅作標記用途（如 `openai-compatible`、`custom`）
- `llm_base_url`: Chat Completions 端點（OpenAI 相容）
- `llm_model`: 模型名稱
- `llm_api_key`: API 金鑰

> 若未填 `llm_api_key`，腳本會嘗試回退到 `~/.openclaw/openclaw.json` 的 OpenAI key。

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

### OpenClaw 預設 Key（可選回退）
若你沒有在 `config.json` 填 `llm_api_key`，可使用 `~/.openclaw/openclaw.json` 的 OpenAI key 作為回退。

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
