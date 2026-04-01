# Morning Brief v2 (Development)

目標：最高可發展性，明確分離「可客製」與「核心流程」。

## v2 configure 欄位（可客製）
- 稱謂：`profile.listener_name`
- 地點：`profile.location`
- topic：`content.topics`
- 風格：`style.*`
- 時長：`voice.duration_sec`
- 男女聲：`voice.gender` + `voice.tts_voice`
- 交付模式：`delivery.mode`（預設 `none`，可選 `telegram`）
- 新聞來源策略：`content.enabled_sources`、`max_candidates_per_source`、`max_candidates_per_topic`、`min_quality_score`
- 來源權重：`content.source_priority`
- topic 白名單來源：`content.topic_source_whitelist`
- 議題黑名單：`content.topic_blacklist`（讓 agent 避開不想用的議題）

> 發報時間不放在 skill configure。
> 排程由客戶自行用 cron/systemd 管理（符合你的原則）。
> skill 預設不綁 channel id，讓不同平台可共用。

## 設計原則
1. Core 與 Configure 分離
2. Agent 只調整 `profiles/user.json`
3. 更新核心時不可覆蓋 `profiles/user.json`
4. 預留 `extensions` 以便未來擴展

## 避坑
- 避免本機寫死路徑
- 避免把 token 寫進 git 追蹤檔
- 避免 long text 一次塞 shell 造成 TTS 截斷
