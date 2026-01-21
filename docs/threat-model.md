# 威脅建模（Threat Model）

版本：1.0
日期：2026-01-22

目的：針對本專案（GitLab MR Reviewer）建立威脅模型，說明系統邊界、主要資產、資料流程、STRIDE 威脅對應，以及可執行的緩解措施與測試建議。

範圍：`src/` 所含核心元件：`CloneManager`、`StateManager`（SQLite + JSON）、`GitLabClient`、`MRScanner`、CLI (`src/main.py`)、以及由 clone 建立的工作目錄（`reviews/`）。另含 CI、依賴套件與外部 GitLab API。

主要資產
- 機密：`GITLAB_TOKEN`（API token）
- 原始碼與邏輯：`src/` 模組
- 克隆的代碼資料（`reviews/<project>/<iid>/`）與 `.mr_info.json`
- 狀態資料庫（SQLite）與 JSON state files
- CI artifacts / SBOM

簡要 DFD（資料流程圖，文字版）
- 使用者 / maintainer → GitLab API ← `GitLabClient`（讀取 MR、提交記錄、檔案差異）
- MR 資訊 → `MRScanner`（過濾）→ `StateManager`（儲存 MR 狀態）
- 經過篩選的 MR → `CloneManager.create_clone()` → 在 `reviews/` 下 `git clone --single-branch`（磁碟）
- CLI（`scan`、`list-clones`、`clean-clone`）與本地 filesystem 操作

Mermaid DFD（可在 GitHub 預覽）:

```mermaid
flowchart LR
	User[User / Maintainer]
	GitLabAPI[GitLab API]
	GitLabClient[GitLabClient]
	MRScanner[MRScanner]
	StateManager[StateManager\n(SQLite + JSON)]
	CloneManager[CloneManager]
	Reviews[reviews/ (cloned repos)]
	CLI[CLI (`src/main.py`)]
	CI[CI / GitHub Actions]
	SBOM[SBOM & Security Reports]

	User -->|requests / CLI| CLI
	CLI -->|calls| MRScanner
	User -->|requests| GitLabAPI
	GitLabAPI -->|API responses| GitLabClient
	GitLabClient --> MRScanner
	MRScanner -->|store state| StateManager
	MRScanner -->|create clone| CloneManager
	CloneManager --> Reviews
	Reviews -->|local files| CLI
	CI -->|runs pip-audit, bandit, sbom| SBOM
	SBOM --> CI
	CI -->|uploads artifacts| Reviews

```


重要信任邊界
- 本地檔案系統（reviews/）與系統使用者權限
- GitLab API 與 token 的網路邊界
- CI runner（執行自動掃描、SBOM）

威脅分類（STRIDE）與示例

1. Spoofing（偽裝身份）
- 威脅：偷用或洩露的 `GITLAB_TOKEN` 被用來呼叫 API；惡意使用者模擬 GitLab webhook/端點。 
- 影響：未授權的 MR 存取、偽造 MR 資料。
- 緩解：使用最小 scope token、在環境變數中只於 CI/部署時注入、強制 rotate、使用短期憑證（若可用）、在日誌中避免紀錄 token。檢查來源 IP（若可行）與 webhook 簽章。

2. Tampering（竄改）
- 威脅：本地 clone 目錄或 `.mr_info.json` 被惡意竄改，使後續處理錯誤或執行惡意程式碼（例如在 CI 上誤執行未信任的程式）。
- 影響：資料不一致、任意程式碼執行（若有執行 clone 內腳本）。
- 緩解：以最低權限建立 clone（不可自動執行 clone 內程式）、限制 `reviews/` 權限（chmod 700）、在需要時使用只讀檢視或容器化隔離 clone（例如 ephemeral containers），並為 `.mr_info.json` 加上簽章或 hash 檢查（若來自可信來源）。

3. Repudiation（否認/不可否認性欠缺）
- 威脅：重要操作（如自動刪除 clone）缺乏足夠可審計紀錄，導致無法追蹤誰/何時觸發。 
- 緩解：建立結構化日誌（包含操作者、時間、MR id、操作），並將日誌集中到安全的存儲（或 CI artifact）以便審計。

4. Information Disclosure（資訊洩露）
- 威脅：敏感 MR 資訊、私有 repo 檔案或 token 被洩露（例如將 `reviews/` 推到公共位置或未加權限的共享目錄）。
- 緩解：不要在 clone 中保留 secrets、確保 `reviews/` 目錄權限與 ACL、在日誌與報告中掩碼敏感欄位（author email、token）。CI artifacts 與 SBOM 應設定為私有或安全上傳。

5. Denial of Service（阻斷服務）
- 威脅：大量 MR 同時掃描或惡意觸發多個 clone，使系統耗盡磁碟或檔案描述符；`pip-audit` 等工具在 CI 上造成過長執行時間（資源耗盡）。
- 緩解：限制並發掃描數量、對 clone 數量或磁碟使用設定配額、在 CI 中設定 timeout、在本地使用異步 queue 與 backoff 策略。

6. Elevation of Privilege（權限提升）
- 威脅：本地程式透過不安全的依賴（如舊版 `filelock`）導致本地檔案被竄改或代理執行，或未受限的套件可在 CI 中導致執行任意程式碼。 
- 緩解：維護依賴更新清單、在 CI 執行 `pip-audit` 與 `bandit`（已加入 workflow）、採用最小化執行環境（container/runner），避免以 root 執行不可信腳本。

專案特有的高風險場景與緩解（優先級）
- 高：`filelock` / `filelock` 的 TOCTOU（如果存在於依賴或被間接使用）→ 立即升級或在關鍵流程中避免使用受影響 API；限制 lock 檔位置權限。
- 高：`GITLAB_TOKEN` 泄漏 → 立即建立政策：最小 scope、PR 模板提醒、CI secret 管理、token rotate 與審計日誌。
- 中：clone 目錄以公開權限存在 → 變更為 `chmod 700`，或將 clone 放在受限容器中。

測試與驗證建議
- 單元測試：模擬 `GitLabClient`，驗證 token 未被寫入日誌與 `.mr_info.json` 的正確性。 
- 整合測試：建立「safety」測試套件，模擬多個 MR 並發掃描以檢驗資源限制與超時行為。 
- 安全測試：在 CI 中定期執行 `pip-audit`、`bandit` 與 SBOM 比對；對 `filelock` 或 fs lock 路徑執行 TOCTOU PoC（受控環境）以驗證是否受影響。 

部署與運營建議
- 最小權限：在文件中強制說明 `GITLAB_TOKEN` 權限需求（scopes）。
- 隔離：考慮使用 ephemeral containers 或 sandboxed VMs 來執行 clones，尤其是在公有 runner 或多人共享環境。 
- 日誌與監控：集中日誌，並設定告警（例如異常大量 clone、刪除操作）。
- 供應鏈安全：在 release pipeline 中產生 SBOM、並在 PR 合併前執行 `pip-audit`。

待辦事項（建議優先順序）
1. 立刻：在 CI 與本地加入 `pip-audit` 與 `bandit`（已完成 workflow）。
2. 立刻：檢查 `requirements.txt` / lockfile，升級 `filelock`、`urllib3`、`setuptools` 等高風險套件。
3. 近期（1-2 週）：實施 `reviews/` 目錄權限硬化與選項化容器化 clone。
4. 中期（數週）：撰寫 `docs/threat-model.md` 的圖像化 DFD（Mermaid 或 drawio），並在 `CONTRIBUTING.md` 中加入安全要求（token 最小 scope、不得在 PR 中提交 token 等）。

擔保與責任
- 建議由專案維護者（owner）指定一位安全負責人以追蹤此威脅模型與修補事項；將高風險修補（如 `filelock`）設定為緊急任務並拆成小 PR。

結語
- 本文件為工程上的實務建議與初步威脅盤點；建議配合攻擊面掃描（SAST/DAST）與滲透測試，並在修補後重複整個威脅建模流程，確保風險已被系統化降低。
