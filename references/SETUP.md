# 初次設定指南

當你第一次安裝此技能後，讓你的 Agent 幫你完成設定：

---

## 1. 設定稱呼

告訴你的 Agent：
```
請幫我設定晨報的稱呼為「[你的名字]」
```

這會影響開頭語：「早安，[名字]」

---

## 2. 設定地點

告訴你的 Agent：
```
請幫我設定晨報天氣地點為「[城市]」
```

支援的城市：
- 台北、Taipei
- 新店、Xindian
- 台中、Taichung
- 高雄、Kaohsiung
- 香港、Hong Kong
- 東京、Tokyo

---

## 3. 設定語系

告訴你的 Agent：
```
請幫我設定晨報語系為「zh-TW」
```

常見值：
- `zh-TW`（繁體中文）
- `zh-CN`（簡體中文）
- `en-US`（英文）

---

## 4. 設定主題

告訴你的 Agent：
```
請幫我設定晨報主題為：
- 國際：world news
- 經濟：economy market
- 科技：AI technology
- 軍事：military war
- 能源：oil energy
```

或選擇其他主題（見 TOPICS.md）

---

## 5. 填入 API Key

編輯 `scripts/config.json`，填入你的 API Key：

```json
{
  "gnews_api_key": "你的GNews API Key",
  "newsdata_api_key": "你的NewsData API Key",
  "telegram_bot_token": "你的Telegram Bot Token",
  "telegram_chat_id": "你的Chat ID"
}
```

---

## 6. 測試

```bash
python3 scripts/daily_podcast.py
```

確認收到 Telegram 語音訊息。

---

## 7. 設定每日自動執行

```bash
crontab -e
```

加入：
```
30 7 * * * cd /path/to/ai2x-skill-morning-brief && python3 scripts/daily_podcast.py
```

---

## 完整範例對話

你可以這樣告訴你的 Agent：

```
請幫我設定晨報：
- 稱呼：Weichien
- 地點：新店
- 語系：zh-TW
- 主題：國際、科技、軍事
- 然後幫我申請 GNews API Key
```

你的 Agent 會一步步引導你完成設定。
