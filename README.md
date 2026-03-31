# AI Morning Briefing Skill

一個 AI 驅動的晨間簡報技能，每天自動收集新聞、天氣資訊，經 AI 翻譯與潤飾後產生**有溫度的個人化語音早報**。

## 功能特色

- 🤖 自動收集新聞（GNews + NewsData.io + BBC RSS）
- 🌤️ Open-Meteo 即時天氣（免費、不需 API Key）
- 🌐 AI 翻譯成繁體中文
- ✨ AI 潤飾（自然對話風格，可交由使用者 Agent）
- 🎙️ 語音輸出（Edge TTS，長文自動分段＋重試＋合併）
- 📤 Telegram 自動推播
- 📋 標題存档（供 Agent 後續查閱）

## 快速開始

### 讓 Agent 安裝

將此 repo URL 告訴你的 Agent：

```
請幫我安裝這個 Skill：https://github.com/ai2x-lab/ai2x-skill-morning-brief
```

你的 Agent 會幫你完成設定。

### 手動安裝

```bash
git clone https://github.com/ai2x-lab/ai2x-skill-morning-brief.git
cd ai2x-skill-morning-brief
```

## 初次設定

詳細步驟請見 [SETUP.md](references/SETUP.md)

快速設定：
1. **稱呼** - 設定你的名字
2. **地點** - 設定天氣地點
3. **主題** - 選擇新聞分類
4. **API Key** - 填入設定檔

## 申請 API Key

| 服務 | 說明 |
|------|------|
| **OpenAI** | 翻譯與潤飾（必要）|
| **GNews** | 新聞來源（免費 100次/天）|
| **NewsData** | 備用新聞（免費 500次/天）|
| **BBC RSS** | 完全免費新聞 |

詳細說明見 [references/CONFIG.md](references/CONFIG.md)

## 自訂主題

編輯 `config.json` 中的 `topics`。

範例見 [references/TOPICS.md](references/TOPICS.md)

## 更新既有安裝（給 Agent）

若使用者已安裝此 skill，請 Agent 用以下步驟更新：

```bash
cd ai2x-skill-morning-brief
git pull origin main
```

更新後注意：
- 不要覆蓋使用者本機 `scripts/config.json`
- 若新增設定欄位，從 `scripts/config.example.json` 合併到本機設定
- 建議更新後手動測一次：
  `python3 scripts/daily_podcast.py`

## 使用方式

```bash
# 手動執行
python3 scripts/daily_podcast.py

# 自動執行
crontab -e
# 30 7 * * * cd /path/to/ai2x-skill-morning-brief && python3 scripts/daily_podcast.py
```

## 輸出檔案

| 檔案 | 位置 |
|------|------|
| 初稿 | `~/clawd/podcast/draft_YYYYMMDD.txt` |
| 潤飾稿 | `~/clawd/podcast/script_YYYYMMDD.txt` |
| 語音 | `~/.openclaw/media/daily_YYYYMMDD.mp3` |
| 標題存档 | `~/clawd/memory/daily-podcast-YYYY-MM-DD.md` |
| 資料包 payload | `~/clawd/podcast/payload_YYYYMMDD.json` |

## 常見問題

### Q: 如何修改分類或關鍵字？
A: 編輯 `config.json` 中的 `topics` 陣列。

### Q: 這個會占用很多 Token 嗎？
A: 不會。Cron Job 隔離執行，不消耗對話上下文。

### Q: Agent 如何知道我問的是晨報內容？
A: Agent 開機時會自動讀取 `memory/daily-podcast-YYYY-MM-DD.md`。

## 授權

MIT License

## 相關資源

- [OpenClaw](https://github.com/openclaw/openclaw)
- [GNews API](https://gnews.io)
- [NewsData.io](https://newsdata.io)
- [Open-Meteo](https://open-meteo.com)
