---
name: morning-brief-v2
description: Agent-first morning brief pipeline with configurable profile, multi-source aggregation, optional delivery adapters, and Edge TTS output.
version: 2.0.0-dev
entrypoint: python3 v2/scripts/runner_v2.py
---

# Morning Brief v2

## 安裝

```bash
git clone https://github.com/ai2x-lab/ai2x-skill-morning-brief.git
cd ai2x-skill-morning-brief
git checkout v2
```

## 初始設定

```bash
cp v2/profiles/user.example.json v2/profiles/user.json
python3 v2/scripts/profile_wizard.py
```

## 必要環境變數

- `MORNING_BRIEF_GNEWS_API_KEY`（必要）
- `MORNING_BRIEF_NEWSDATA_API_KEY`（可選）
- `MORNING_BRIEF_TELEGRAM_BOT_TOKEN`（只有 `delivery.mode=telegram` 才需要）
- `MORNING_BRIEF_TELEGRAM_CHAT_ID`（可選，覆蓋 profile）

## 測試

### 1) 乾跑（不發送）
```bash
MORNING_BRIEF_GNEWS_API_KEY=xxx python3 v2/scripts/runner_v2.py --dry-run
```

預期輸出包含：
- `ok: true`
- `audio_path`
- `packet_path`

### 2) Telegram 發送（可選）
將 `v2/profiles/user.json` 設為：
```json
"delivery": { "mode": "telegram", "telegram_chat_id": "你的chat_id" }
```
然後：
```bash
MORNING_BRIEF_GNEWS_API_KEY=xxx MORNING_BRIEF_TELEGRAM_BOT_TOKEN=xxx python3 v2/scripts/runner_v2.py
```

## 執行模式

- `render.mode=agent`: 先交給 agent 潤飾
- `render.fallback_mode=self`: agent 失敗時回退到 self

## 設計邊界

- 排程時間由使用者自行用 cron/systemd 管理
- v2 預設 `delivery.mode=none`，不綁任何通道
- agent 僅應調整 `v2/profiles/user.json`，不要改 core
