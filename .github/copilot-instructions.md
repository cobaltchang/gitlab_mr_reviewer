# GitLab MR Reviewer - AI 代理指引

## 項目概覽

一個 Python CLI 工具，自動掃描 GitLab 上的 Merge Requests 並管理本地 git worktrees 以進行程式碼審查。系統會獲取 MR 元資料、根據狀態（WIP/草稿）進行篩選，並為並行審查工作流程建立隔離的 git worktrees。

## 架構

### 核心元件

- **Config** ([src/config.py](src/config.py))：環境變數驅動的設定，包括必要項（GitLab URL/令牌/專案）和可選項（路徑、日誌級別、重試次數）
- **GitLabClient** ([src/gitlab_/client.py](src/gitlab_/client.py))：`python-gitlab` 的簡潔包裝器，用於 MR 查詢和專案操作
- **MRScanner** ([src/scanner/mr_scanner.py](src/scanner/mr_scanner.py))：掃描專案、篩選 MRs（排除 WIP/草稿）、返回 `ScanResult` 物件
- **StateManager** ([src/state/manager.py](src/state/manager.py))：雙儲存體（SQLite + JSON）用於 MR 狀態追蹤和掃描歷史
- **WorktreeManager** ([src/worktree/manager.py](src/worktree/manager.py))：使用 `GitPython` 和 subprocess 進行 Git worktree 生命週期管理（建立/更新/清理）
- **Main CLI** ([src/main.py](src/main.py))：Click 式 CLI，提供 `scan`、`list-worktrees` 和 `clean-worktree` 命令

### 資料流程

```
Config.from_env() → GitLabClient → MRScanner.scan()
                                     └→ StateManager (儲存/檢查狀態)
                                        └→ WorktreeManager (建立/更新 worktrees)
```

## 關鍵模式

### 1. 異常層級結構
使用來自 [src/utils/exceptions.py](src/utils/exceptions.py) 的自訂異常：
- `ConfigError`：設定無效或缺失
- `GitLabError`：API 失敗或連接問題
- `WorktreeError`：Git worktree 操作失敗
- `StateError`：資料庫/JSON 持久化失敗
- `GitError`：Git 命令執行失敗

**模式**：捕捉特定異常、記錄上下文、重新拋出或適當處理。

### 2. 全域元件初始化
[src/main.py](src/main.py) 使用在 `init_app()` 中初始化的模組層級全域變數：
```python
config: Optional[Config] = None
gitlab_client: Optional[GitLabClient] = None
mr_scanner: Optional[MRScanner] = None
state_manager: Optional[StateManager] = None
worktree_manager: Optional[WorktreeManager] = None
```
每個 Click 命令在使用元件之前都會呼叫 `init_app()`。此模式避免了循環導入，但需要小心的初始化順序。

### 3. 環境變數配置
[src/config.py](src/config.py) 使用 `Config.from_env()` 搭配必需的環境變數：
- `GITLAB_URL`：GitLab 執行個體 URL
- `GITLAB_TOKEN`：存取令牌
- `GITLAB_PROJECTS`：逗號分隔的專案清單

可選變數有合理的預設值（例如 `STATE_DIR="./state"`、`LOG_LEVEL="INFO"`）。路徑中始終使用 `Path.expanduser()` 展開 `~`。

### 4. 雙儲存體策略
[src/state/manager.py](src/state/manager.py) 同時支援 SQLite 和 JSON：
- SQLite 用於結構化查詢（生產環境）
- JSON 用於可讀的除錯
首次執行時初始化資料庫架構，冪等操作使用 `CREATE TABLE IF NOT EXISTS`。

### 5. Git Worktree MR 整合
[src/worktree/manager.py](src/worktree/manager.py) 使用 GitLab 的虛擬 refs：
```bash
git fetch origin refs/merge-requests/{iid}/head
git worktree add <path> FETCH_HEAD
```
此模式避免在主倉庫中檢出 MR 分支。每個 MR 都在與專案結構相符的隔離 worktree 目錄中。

### 6. 篩選管道
[src/scanner/mr_scanner.py](src/scanner/mr_scanner.py) 實現多階段篩選：
- 排除 WIP（work_in_progress 旗標）
- 排除草稿（draft 旗標）
- 可擴展：依照 `_filter_mrs` 模式添加新的篩選方法

## 開發工作流程

### 測試（需要 TDD）
```bash
pytest                          # 執行所有測試
pytest tests/test_config.py    # 執行特定模組
pytest --cov=src               # 覆蓋率報告
```
測試模式：對環境變數使用 `monkeypatch`、對檔案操作使用 `tmp_path`、對 API 樁使用 `mocker`。

### 本地執行
```bash
python -m src.main scan --dry-run                    # 預覽而不實際執行
python -m src.main scan --exclude-wip --exclude-draft
python -m src.main list-worktrees
python -m src.main clean-worktree --iid 123
```

### 優先理解的關鍵檔案
1. [spec.md](spec.md)：完整的需求和設計決策
2. [CONTRIBUTING.md](CONTRIBUTING.md)：TDD 工作流程和程式碼結構規則
3. [src/main.py](src/main.py)：展示元件編排的進入點
4. [src/config.py](src/config.py)：設定系統（必讀）

## 跨元件通訊

- **GitLabClient → StateManager**：掃描後儲存 MR 狀態以追蹤更新
- **MRScanner → StateManager**：篩選前檢查現有狀態以避免冗餘 API 呼叫
- **StateManager → WorktreeManager**：建立 worktrees 前獲取已儲存的 MR 資訊
- **所有元件 → Logger**：透過 [src/logger/__init__.py](src/logger/__init__.py) 進行中央日誌記錄

## 常見陷阱

- **未展開路徑**：始終使用 `Path().expanduser()` 支援 `~`
- **忘記狀態同步**：StateManager 必須在掃描之前初始化
- **忽略草稿旗標**：不同 GitLab 版本使用不同的屬性名稱；同時檢查 `draft` 和 `work_in_progress`
- **原始 subprocess 呼叫**：使用 WorktreeManager 方法，不要在其他模組中使用裸 `git` 命令
- **缺少錯誤上下文**：在日誌訊息中包含專案/MR IID 以便除錯

## 新增功能

1. 先添加測試（TDD）：在 `tests/test_*.py` 中建立測試
2. 在適當的模組中實現（尊重單一職責原則）
3. 如果功能需要持久化，更新 StateManager
4. 如果是用戶面向功能，在 [src/main.py](src/main.py) 中添加 Click 命令
5. 在 [spec.md](spec.md) 中進行文件記錄
