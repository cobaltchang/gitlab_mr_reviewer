```markdown
# 事件回應手冊

目的：提供一套可重複的步驟，用於回應本專案中被通報或偵測到的安全事件。

1. 初步分級（Triage）
- 在 Issue tracker 中確認收到報告（並於內部通道中回覆），24 小時內回應。
- 依據對機密性、完整性與可用性的影響評定嚴重性（Critical / High / Medium / Low）。

2. 隔離（Containment）
- 若為程式碼/CI 問題：立即停用受影響的 workflow 或在必要時撤銷已洩露的 secret。
- 若為相依性 CVE：建立優先 PR 以修補或採用緩解措施（constraints / 回滾）。

3. 調查（Investigation）
- 收集證據：`installed.txt`、`pip_audit_report.json`、`sbom.json`、相關日誌。
- 在隔離環境中嘗試復現問題。

4. 修復（Remediation）
- 套用補丁或升級相依，執行測試並依 PR 流程合併至主分支。
- 若為公開漏洞，協調通報時程與對外說明。

5. 事件後（Post-incident）
- 發佈事件摘要（必要時遮蔽敏感內容）與檢討；旋轉受影響的憑證。

```