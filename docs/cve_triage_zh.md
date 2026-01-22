```markdown
# CVE 分級與修復流程

目的：提供一致的 CVE 分級、指派與 SLA，以符合 CRA / IEC 62443 的期望。

1. 分級（Classification）
- Critical：已被利用或可在預設設定下執行遠端程式碼執行 — SLA：7 天內修補，30 天內發布修補版本。
- High：具本地提權或資料外洩風險 — SLA：14 天內修補，45 天內發布修補版本。
- Medium/Low：資訊性或低影響 — SLA：90 天內處理。

2. 指派（Assignment）
- 建立 GitHub Issue，標籤為 `security` 並指派給安全負責人。

3. 修復工作流程（Fix workflow）
- 建立分支 `chore/security/upgrade-<pkg>`，以最小版本變更為原則。
- 在 CI 中執行測試與安全掃描；若 CI 失敗則重試與調整。

4. 對外揭露（Disclosure）
- 根據嚴重性協調公開揭露時程；對 Critical/High 等級，在修補完成前避免公開通告。

```