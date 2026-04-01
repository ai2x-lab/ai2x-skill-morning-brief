# v2 Core (immutable-by-agent)

這裡放 v2 核心流程程式碼。原則：
- Agent 不應直接修改 core；只調整 `profiles/user.json`
- Core 更新可直接覆蓋
- 啟動前必須先載入 merged profile（default+user+env）
