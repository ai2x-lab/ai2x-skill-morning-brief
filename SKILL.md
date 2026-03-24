---
name: daily-podcast
description: 晨間語音早報產生器。當用戶說「生成早報」、「播放晨報」、「今日摘要」、「morning podcast」、「daily podcast」或需要產生每日益智與新聞摘要並用語音播放時使用此技能。
---

# Daily Podcast - 晨間語音早報產生器

## 功能

- 🤖 **自動收集**：GNews + NewsData.io 新聞來源
- 🌤️ **天氣資訊**：新店/台北即時天氣
- 🌐 **AI 翻譯**：英文新聞翻譯成繁體中文（支援 auto fallback）
- ✨ **AI 潤飾**：初稿轉為有溫度的個人化版本（local 不通時自動降級）
- 🎙️ **語音輸出**：Edge TTS 文字轉語音
- 📤 **推播通知**：可配置（telegram/stdout/none，不綁定 Telegram）
- 📋 **標題存档**：供 Agent 後續查閱

## 前置需求

| 需求 | 說明 |
|------|------|
| Python 3 | 系統已有 |
| Edge TTS | 建議先安裝 `npm install -g node-edge-tts`（v17.3 會嘗試自動安裝） |
| OpenClaw 本機 Gateway | 預設 AI 翻譯與潤飾（免填外部 key） |
| OpenAI/MiniMax API Key（可選） | local 不可用時 fallback |
| Delivery mode | `none`（預設）/`stdout`/`telegram` |
| GNews API Key | 新聞來源（免費申請）|
| NewsData API Key | 備用新聞來源（免費申請）|
| Telegram Bot | 推播通知 |

詳見 [CONFIG.md](references/CONFIG.md)

## 安裝

```bash
# 1. 複製技能目錄
cp -r daily-podcast ~/clawd/skills/

# 2. 複製設定檔
cp ~/clawd/skills/daily-podcast/scripts/config.example.json \
   ~/clawd/skills/daily-podcast/scripts/config.json

# 3. 編輯設定（可直接使用本機模型，不必填 AI key）
vim ~/clawd/skills/daily-podcast/scripts/config.json
```

## 設定自訂

### 自訂主題

編輯 `config.json` 中的 `topics`：

```json
{
  "topics": [
    ["國際", "world news"],
    ["經濟", "stock market"],
    ["科技", "AI technology"],
    ["軍事", "military"],
    ["能源", "oil energy"]
  ]
}
```

主題範例見 [TOPICS.md](references/TOPICS.md)

### 自訂分類數量

```json
{
  "news_count": 2
}
```

建議 1-3，太多會讓語音過長。

### 自訂語音長度

```json
{
  "voice_max_duration": 300
}
```

單位：秒，預設 300 秒（5 分鐘）。

### 自訂新聞來源

```json
{
  "sources": ["gnews", "newsdata"]
}
```

- `["gnews"]` - 只用 GNews
- `["newsdata"]` - 只用 NewsData  
- `["gnews", "newsdata"]` - 同時使用

## 使用方式

```bash
# 手動執行
python3 ~/clawd/skills/daily-podcast/scripts/daily_podcast.py

# Cron 排程（每天 7:30）
30 7 * * * cd /home/ubuntu && python3 ~/clawd/skills/daily-podcast/scripts/daily_podcast.py
```

## 流程

```
1. 收集天氣
2. 抓取新聞（GNews → NewsData 備用）
3. AI 翻譯成繁體中文
4. AI 潤飾（有溫度的版本）
5. 產生語音
6. 發送到 Telegram
7. 存档標題供 Agent 查閱
```

## Agent 使用

當用戶要求生成早報時，執行：

```bash
python3 ~/clawd/skills/daily-podcast/scripts/daily_podcast.py
```

Agent 開機時會自動讀取 `memory/daily-podcast-YYYY-MM-DD.md`，了解當天廣播內容。

## 輸出檔案

| 檔案 | 位置 |
|------|------|
| 初稿 | `~/clawd/podcast/draft_YYYYMMDD.txt` |
| 潤飾稿 | `~/clawd/podcast/script_YYYYMMDD.txt` |
| 語音 | `~/.openclaw/media/daily_YYYYMMDD.mp3` |
| 標題存档 | `~/clawd/memory/daily-podcast-YYYY-MM-DD.md` |

## 故障排除

### 發音不清楚
潤飾時可要求「使用簡單詞彙，適合語音朗讀」

### 語音太長
減少 `news_count` 或減少 `topics` 數量

### 無法發送到 Telegram
檢查 `telegram_bot_token` 和 `telegram_chat_id` 是否正確

### 新聞重複
增加 `sources` 只用其中一個來源

## Agent 回報

當用戶問「今天晨報有哪些內容」時：
1. 讀取 `~/clawd/memory/daily-podcast-YYYY-MM-DD.md`
2. 回報標題列表和分類

## Token 消耗說明

這是隔離任務，不消耗對話上下文：
- Cron Job 直接執行，不走主對話
- 只消耗 AI 潤飾的 API token
