````markdown
**安全自動化與修復流程（可重用）**

概述
- 本文件說明一套可重複、可在其他 Python 專案重用的安全掃描與修復工作流程。

目標
- 持續偵測易受攻擊的相依套件並記錄 SBOM。
- 為維護者建立可行動的產物（Issue、PR）。
- 將執行時依賴（`requirements.txt`）與開發工具依賴（`dev-requirements.txt`）分離。

核心元件
- 可重用工作流程：`.github/workflows/security-scan-reusable.yml`，可由其他 repo 以 `workflow_call` 呼叫。
- PR 層級檢查：`.github/workflows/pr-security-check.yml`，於 Pull Request 上執行。
- 本地腳本：`scripts/run_security_checks.sh`（開發者使用）。
- 範本：安全升級的 PR 範本，以及漏洞通報的 Issue 範本。

流程（高階）
1) 探測
   - 以排程或手動觸發呼叫可重用 workflow。
   - 使用 `pip-audit` 掃描宣告的執行時相依並輸出 JSON。
   - 使用 `cyclonedx-py` 產生 `sbom.json` 供稽核使用。
2) 分級（Triage）
   - workflow 會建立 GitHub Issue 摘要掃描結果。
   - 指派對應負責人（由 `CODEOWNERS` 決定）。
3) 修復
   - 若為執行時漏洞：逐套件建立分支並開 Draft PR（依專案政策）。
   - 若為開發工具：更新 `dev-requirements.txt` 並在 CI 驗證後合併。
4) 驗證
   - PR 必須通過 `pr-security-check`（測試 + pip-audit + SBOM 產生）後方可合併。
5) 發佈與稽核
   - 在發行（release）時附上最終 `sbom.json`，或將其儲存在 `sbom/` 做為稽核用。

如何在其他倉庫重用
1) 將 `.github/workflows/security-scan-reusable.yml` 複製到目標倉庫。
2) 新增一個排程 workflow 呼叫它，例如：

```yaml
on:
  schedule:
    - cron: '0 3 * * 1'

jobs:
  call-security:
    uses: <owner>/<repo>/.github/workflows/security-scan-reusable.yml@main
    with:
      requirements-path: requirements.txt
      dev-requirements-path: dev-requirements.txt
      run-tests: true
      create-prs: false
```

3) 新增 `pr-security-check.yml` 或依據 CI 結構調整 PR 驗證流程。

本地開發者腳本
- 執行完整本地掃描並產生 SBOM：

```bash
./scripts/run_security_checks.sh
```

注意事項與最佳實務
- 優先建立小範圍、單套件的升級 PR 以利回滾。
- 將 SBOM 的產生保留於 CI，以避免產生過多自動 commit；僅在 release 時將 SBOM 加入版本。
- 使用 `CODEOWNERS` 將安全相關 PR 指派給合適的審查者。

````
