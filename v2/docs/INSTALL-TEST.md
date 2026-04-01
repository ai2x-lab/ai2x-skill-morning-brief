# v2 安裝測試 SOP（5 分鐘）

1. checkout v2 分支
2. 建立 `v2/profiles/user.json`
3. 設定 `MORNING_BRIEF_GNEWS_API_KEY`
4. 執行 dry-run
5. 確認 `audio_path` + `packet_path` 存在
6. （可選）切 `delivery.mode=telegram` 實發

## 驗收標準
- dry-run 成功（`ok=true`）
- packet JSON 有多來源候選
- audio 可播放、非極短檔
- 若 `render.mode=agent` 失敗，會 fallback self 且不中斷
