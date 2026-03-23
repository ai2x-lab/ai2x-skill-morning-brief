# AI Morning Briefing Skill

一個 AI 驅動的晨間簡報技能，每天自動收集新聞、天氣資訊，經 AI 翻譯與潤飾後產生**有溫度的個人化語音早報**。

## 功能特色

- 🤖 自動收集新聞（GNews + NewsData.io）
- 🌤️ 即時天氣資訊
- 🌐 AI 翻譯成繁體中文
- ✨ AI 潤飾（自然對話風格）
- 🎙️ 語音輸出（Edge TTS）
- 📤 Telegram 自動推播
- 📋 標題存档（供 Agent 後續查閱）

## 前置需求

| 需求 | 說明 |
|------|------|
| Python 3 | 系統已有 |
| Edge TTS | `npm install -g node-edge-tts` |
| OpenAI API Key | AI 翻譯與潤飾 |
| GNews API Key | 新聞來源（免費申請）|
| NewsData API Key | 備用新聞來源（免費申請）|
| Telegram Bot | 推播通知 |

## 快速安裝

### 1. 讓 Agent 安裝

將此 repo URL 告訴你的 Agent：

```
請幫我安裝這個 Skill：https://github.com/ai2x-lab/ai2x-skill-morning-brief
```

你的 Agent 會：
1. Clone 此 repo
2. 設定 config.json
3. 設定 Cron Job

### 2. 手動安裝

```bash
# Clone repo
git clone https://github.com/ai2x-lab/ai2x-skill-morning-brief.git
cd ai2x-skill-morning-brief

# 複製設定檔
cp scripts/config.example.json scripts/config.json

# 編輯設定（填入你的 API Key）
vim scripts/config.json
```

## 申請 API Key

### GNews API（免費）
1. 前往 https://gnews.io/register
2. 免費額度：100次/天，12小時延遲

### NewsData.io（免費）
1. 前往 https://newsdata.io/register
2. 免費額度：500次/天

### Telegram Bot
1. @BotFather 傳送 `/newbot`
2. 取得 Bot Token
3. 傳訊息給 @userinfobot 取得 Chat ID

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

## 設定自訂

### config.json 欄位說明

```json
{
  "location": "Taipei,Taiwan",
  "topics": [
    ["國際", "world news"],
    ["經濟", "economy market"],
    ["科技", "AI technology"],
    ["軍事", "military war"],
    ["能源", "oil energy"]
  ],
  "news_count": 2,
  "sources": ["gnews", "newsdata"]
}
```

### 自訂主題

編輯 `topics` 陣列。詳見 [references/TOPICS.md](references/TOPICS.md)。

### 範例主題

```json
// 籃球迷
["NBA 湖人", "NBA Lakers LeBron"],
["NBA 勇士", "NBA Warriors Curry"]

// 藝術愛好者
["藝術展覽", "art exhibition museum"],
["電影新片", "Hollywood movie release"]

// 商務人士
["美股市場", "US stock market Dow Jones"],
["加密貨幣", "bitcoin cryptocurrency"]
```

## 使用方式

```bash
# 手動執行測試
python3 scripts/daily_podcast.py

# 設定每天自動執行
crontab -e
# 加入這行（每天 7:30 執行）：
30 7 * * * cd /path/to/ai2x-skill-morning-brief && python3 scripts/daily_podcast.py
```

## 輸出檔案

| 檔案 | 位置 |
|------|------|
| 初稿 | `~/clawd/podcast/draft_YYYYMMDD.txt` |
| 潤飾稿 | `~/clawd/podcast/script_YYYYMMDD.txt` |
| 語音 | `~/.openclaw/media/daily_YYYYMMDD.mp3` |
| 標題存档 | `~/clawd/memory/daily-podcast-YYYY-MM-DD.md` |

## 常見問題

### Q: Agent 如何知道我問的是晨報內容？
A: Agent 開機時會自動讀取 `memory/daily-podcast-YYYY-MM-DD.md`，了解當天廣播了什麼。

### Q: 如何修改分類或關鍵字？
A: 編輯 `config.json` 中的 `topics` 陣列。

### Q: 這個會占用很多 Token 嗎？
A: 不會。Cron Job 隔離執行，不消耗對話上下文。

## 授權

MIT License

## 相關資源

- [OpenClaw](https://github.com/openclaw/openclaw)
- [GNews API](https://gnews.io)
- [NewsData.io](https://newsdata.io)
