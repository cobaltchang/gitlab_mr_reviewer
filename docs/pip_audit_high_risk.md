# pip-audit 高風險套件與 PR 升級建議

此檔案依據本地 `pip-audit` 報告整理出需優先處理的套件、建議升級版本與 PR 建議範本。

優先級規則：以可導致資料損毀、遠端/本地提權、RCE 或可影響 CI/打包完整性的漏洞為高優先。

1) `filelock`  (installed: 3.19.1) — 修補版本: `3.20.1` / `3.20.3`
- 風險：TOCTOU symlink race，可能導致任意檔案截斷或資料損毀（高）
- 建議 PR 標題：chore(deps): upgrade filelock to 3.20.1 to fix TOCTOU CVE
- 變更內容：更新 `requirements.txt` 與鎖版檔（若有），執行 CI 測試。
- 測試：在 CI 執行完整 test-suite，並針對可能使用 `filelock` 的路徑操作執行基本整合測試。

2) `urllib3` (installed: 1.21.1) — 修補版本: `>=1.26.17` 或 `2.0.6+` 等
- 風險：多項 redirect/DoS/信息洩漏 CVE，影響 HTTP 客戶端安全（高/中）
- 建議 PR 標題：chore(deps): bump urllib3 to 1.26.19+ to address multiple CVEs
- 變更/測試：執行整合呼叫到受信任端點、檢查 redirect/Authorization header 處理。

3) `setuptools` (installed: 49.2.1) — 修補版本: `>=70.0.0` / `65.5.1` / `78.1.1`
- 風險：可能的 RCE / 路徑穿越，影響打包與安裝流程（高）
- 建議 PR 標題：chore(deps): upgrade setuptools to 70.0.0+

4) `pillow` (installed: 8.0.1) — 修補版本: `>=8.2.0`, 若能升到 `10.x` 更佳
- 風險：多處解析/記憶體/RCE/DoS 問題，影響任何處理圖片的路徑（高）
- 建議：升級並在 CI 中加入對主要影像解析流程的回歸測試。

5) `pyinstaller` (installed: 3.4) — 修補版本: `>=5.13.1` / `6.0.0+`
- 風險：本地提權 / 不安全 bootstrap，若專案使用 pyinstaller 發行需優先處理（高）

6) `numpy` (installed: 1.19.4) — 修補版本: `>=1.21` / `1.22`
- 風險：buffer overflow / API edge-case，可導致 DoS 或記憶體問題（中/高視使用情境）

7) `certifi`, `future`, `idna`, `wheel` 等若有可用修補版本亦應同步處理。

PR 範例 checklist（在 PR description 中貼上）：
- 升級套件與更新 `requirements.txt`（或 `constraints.txt` / lockfile）
- 在 CI 上執行：`pytest -q`、`bandit -r src/`、`pip-audit`（本次升級檢查）
- 若為重要套件（filelock、urllib3、setuptools、pillow）：增加相依路徑的回歸測試或模擬場景
- 若升級造成相容性問題：回滾計畫與回溯修補時間窗口說明（SLA）

建議執行流程（短期行動）：
- 建立分支 `chore/security/upgrade-deps-high`，拆分多個小 PR（每個 PR 單一套件或密切相關套件），以減低回歸風險
- 在每個 PR 中加入維護者核准，並在 merge 前確保 CI 與安全掃描均通過

我已將完整 `pip-audit` JSON 報告儲存為 `pip_audit_report.json`。要我接著為每個高風險項自動開 PR 分支與 draft PR 模板嗎？
