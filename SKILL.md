---
name: daily-podcast
description: 晨間語音早報產生器。當用戶說「生成早報」、「播放晨報」、「今日摘要」、「morning podcast」、「daily podcast」或需要產生每日益智與新聞摘要並用語音播放時使用此技能。
---

# Daily Podcast - 晨間語音早報產生器

## 功能

- 🤖 **自動收集**：GNews + NewsData.io 新聞來源
- 🌤️ **天氣資訊**：新店/台北即時天氣
- 🗓️ **民俗行事曆**：整合農曆/節慶提醒素材（透過 `folk_calendar_brief.js`）
- 🌐 **AI 翻譯**：英文新聞翻譯成繁體中文
- ✨ **AI 潤飾**：初稿轉為有溫度的個人化版本
- ⏱️ **可控長度**：依 `voice_max_duration` 目標輸出，預設約 5 分鐘
- 🎙️ **語音輸出**：Edge TTS 文字轉語音
- 📤 **推播通知**：自動發送到 Telegram
- 📋 **標題存档**：供 Agent 後續查閱

## 前置需求

| 需求 | 說明 |
|------|------|
| Python 3 | 系統已有 |
| Edge TTS | `npm install -g node-edge-tts` |
| LLM API Key（OpenAI 相容） | AI 翻譯與潤飾（可用客戶自有模型） |
| GNews API Key | 新聞來源（免費申請）|
| NewsData API Key | 備用新聞來源（免費申請）|
| Telegram Bot | 推播通知 |

詳見 [CONFIG.md](references/CONFIG.md)

## 安裝（連動兩個 skills）

> 建議一起安裝：
> 1) `daily-podcast`（晨報主流程）
> 2) `lunar-calendar`（民俗行事曆/節慶能力，讓內容更完整）

```bash
# 1. 安裝 daily-podcast
cp -r daily-podcast ~/clawd/skills/

# 2. 安裝 lunar-calendar（供民俗行事曆素材）
cp -r lunar-calendar ~/clawd/skills/

# 3. 複製設定檔
cp ~/clawd/skills/daily-podcast/scripts/config.example.json \
   ~/clawd/skills/daily-podcast/scripts/config.json

# 4. 編輯設定（填入你的 API Key）
vim ~/clawd/skills/daily-podcast/scripts/config.json
```

民俗素材來源：
- `twcal`（來自 lunar-calendar skill）
- `~/clawd/tools/folk_calendar_brief.py`

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

### 自訂語音長度（建議約 5 分鐘）

```json
{
  "voice_max_duration": 300
}
```

單位：秒，預設 300 秒（約 5 分鐘）。
此值會影響 AI 潤飾字數目標（約 5 分鐘口播長度）。

### 自訂新聞來源

```json
{
  "sources": ["gnews", "newsdata"]
}
```

- `["gnews"]` - 只用 GNews
- `["newsdata"]` - 只用 NewsData  
- `["gnews", "newsdata"]` - 同時使用

## 使用前提醒（重要）

Agent 第一次部署時，請先詢問使用者希望的晨報稱呼，並寫入 `scripts/config.json` 的 `listener_name`。

例如：

```json
{
  "listener_name": "阿美姐"
}
```

避免使用固定預設稱呼造成違和感。

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
