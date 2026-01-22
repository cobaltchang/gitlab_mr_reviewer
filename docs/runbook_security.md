# Security Runbook — GitLab MR Reviewer

目標：定義自動化掃描、通報、升級與驗證的標準作業程序，並提供可重用的步驟供其他專案採用。

1) 監測與觸發
- 每週定期掃描（由 `scheduled-security.yml` 或外部呼叫 `security-scan-reusable.yml` 觸發）。
- 當 `pip-audit` 或其他工具在 CI/排程中發現高/關鍵漏洞時，workflow 會上傳 `pip_audit_report.json` 与 `sbom.json` 並建立 Issue（自動化摘要）。

2) 初步 triage
- 負責人：指派 `CODEOWNERS` 或 `security` 團隊成員。
- 確認漏洞是否影響 runtime（列於 `requirements.txt`）或僅為 dev-tool（`dev-requirements.txt`）。
- 若為 false positive，附上證據並關閉 Issue。

3) 風險分類與優先順序
- Critical/High：立即建立 hotfix 分支或 patch，並通知利害關係人（Slack/Email）。
- Medium/Low：以常規維護分支（單套件 PR）處理，安排週期性合併。

4) 升級步驟（runtime）
- 建立分支：`chore/security/upgrade-<pkg>-<version>`。
- 在乾淨環境執行（本地或 CI）：

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pytest
bandit -r src/ || true
pip-audit -r requirements.txt -f json -o pip_audit_pr.json || true
```

- 若測試通過且無高/關鍵新警示，開 Draft PR（使用 PR 模板），將 `sbom.json` 與 `pip_audit_pr.json` 作為 artifacts（CI 上傳）。
- 若失敗，回退版本或進行相容性修正，並在 Issue 中記錄原因與後續計畫。

5) 升級步驟（dev-only）
- 直接更新 `dev-requirements.txt`，在 CI 驗證即合併；不需立即更新 release SBOM。

6) 緊急修補（hotfix）
- 若有已被利用漏洞：建立 hotfix 分支、更新 `requirements.txt`、產生 SBOM、立刻合併並釋出新版本。
- 按 `docs/incident_response.md` 通知受影響方並跟進 CVE/公告。

7) 驗證與文件化
- PR 合併後：在 release pipeline 中附上最終 `sbom.json`；在 release note 註明安全修補。
- 更新 `docs/pip_audit_high_risk.md`、`docs/security_checklist.md` 與 `docs/security_process.md`（如有新步驟）。

8) 回退計畫
- 若升級引入重大回歸：
  - 立即回退合併（revert PR），並建立追蹤 Issue。
  - 若需要，重建以指定次佳版本並重試驗證。

9) 聯絡清單
- 指派 `CODEOWNERS` 中的成員為首要聯絡人；若為重大事件，使用 `docs/incident_response.md` 中的通報流程。

10) 常用命令摘要

```bash
# 產生 SBOM 與 pip-audit JSON
./scripts/run_security_checks.sh

# 在 PR workflow 中自動產生 artifacts（由 CI 執行）
# 可手動呼叫 reusable workflow 或使用 schedule.
```

11) 可重用性
- 將 `.github/workflows/security-scan-reusable.yml` 引用到其他 repo 的 schedule 或 manual trigger，可水平展開至多個專案。

附錄：範例溝通模板、SLA 與審查清單見 `docs/security_process.md` 與 `docs/security_checklist.md`。
