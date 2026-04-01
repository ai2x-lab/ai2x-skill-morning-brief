# Morning Brief v2 (Core/Profile Split)

這是 v2 架構（開發中），目標：
- 核心流程可穩定更新（Core）
- 使用者客製不被覆蓋（Profile）
- 升級有版本與遷移（Schema + Migration）

## 設計原則
1. Core 與 Profile 分離
2. Profile 版本化（`profile_version`）
3. Schema 驗證（允許 extensions）
4. 更新只覆蓋 Core，保留 `profiles/user.json`

## 避坑清單（已踩過）
- 不把長文本直接塞進 shell command（避免 TTS 截斷）
- 不依賴單機寫死路徑（`/home/...`）
- 不把 token 硬寫在 repo 追蹤檔
- 不讓 agent 任意改 core 檔案
