# GitLab MR Reviewer - 項目規範

## 1. 項目概述

GitLab MR Reviewer是一個自動化的Merge Request掃描和本地審查工具。它定期掃描GitLab上的MR，自動在本地建立獨立的 git clone（single-branch 模式），便於開發者進行程式碼審查。

## 2. 核心功能

### 2.1 MR 掃描功能

- 支援多個專案的掃描
- 支援排除 WIP 和草稿 MR
- 增量掃描和狀態追蹤
- 自定義篩選條件

### 2.2 MR Clone 管理功能

- 使用 `git clone -b <source_branch> --single-branch` 建立獨立的 MR 副本
- 每個 MR 對應一個獨立目錄（`reviews/<project>/<iid>/`）
- 若目錄已存在則刪除後重新 clone（確保同步最新狀態）
- .mr_info.json 元資料儲存
- 支援試執行模式

### 2.3 設計決策

採用 single-branch clone 而非 git worktree 的原因：
- **簡化依賴**：不需要預先存在的主倉庫
- **避免 force-push 問題**：重新 clone 即可取得最新狀態，無需處理 reset --hard
- **隔離性更好**：每個 MR 完全獨立，互不影響
- **網路頻寬不是瓶頸**：內網環境且 repo 通常不大

### 2.3 狀態管理

- SQLite和JSON雙存儲
- MR狀態追蹤
- 掃描歷史記錄
- 自動建立和初始化

## 3. 架構設計

### 3.1 模組結構

```
src/
├── __init__.py          # 包初始化和版本
├── config.py            # 設定管理
├── main.py              # CLI主應用
├── logger/              # 日誌模組
│   └── __init__.py
├── utils/               # 工具模組
│   ├── __init__.py
│   └── exceptions.py    # 自訂異常定義
├── gitlab_/             # GitLab API客戶端
│   ├── __init__.py
│   ├── client.py        # GitLab API wrapper
│   └── models.py        # 資料模型
├── scanner/             # MR掃描引擎
│   ├── __init__.py
│   └── mr_scanner.py    # 掃描和篩選邏輯
├── state/               # 狀態管理
│   ├── __init__.py
│   ├── manager.py       # 狀態管理器
│   └── models.py        # 狀態資料模型
└── worktree/            # Worktree管理
    ├── __init__.py
    └── manager.py       # Worktree生命週期管理

tests/
├── __init__.py
├── conftest.py          # pytest設定
├── test_config.py       # 配置測試
├── test_exceptions.py   # 異常測試
├── test_gitlab_client.py # GitLab客戶端測試
├── test_scanner.py      # 掃描器測試
└── test_state_manager.py # 狀態管理測試

docs/
├── installation.md      # 安裝指南
├── configuration.md     # 配置說明
└── usage.md            # 使用指南
```

### 3.2 依賴關係

```
python-gitlab>=3.0.0     # GitLab API
GitPython>=3.1.0         # Git操作
click>=8.1.0             # CLI框架
python-dotenv>=0.19.0    # 環境變數
pytest>=7.0.0            # 測試框架
pytest-mock>=3.10.0      # Mock 支援
```

## 4. 資料流程

### 4.1 掃描流程

```
1. 載入設定 (Config)
   ↓
2. 初始化GitLab客戶端
   ↓
3. 掃描各專案的MR
   ↓
4. 篩選MR (排除WIP、草稿等)
   ↓
5. 檢查狀態
   ↓
6. 建立MR clone (若已存在則刪除重建)
   ↓
7. 記錄狀態
   ↓
8. 輸出結果和日誌
```

### 4.2 MR Clone 建立流程

```
1. 計算目標路徑: reviews/<project_name>/<iid>/
   ↓
2. 若目錄已存在 → 刪除整個目錄
   ↓
3. 執行: git clone -b <source_branch> --single-branch <repo_url> <path>
   ↓
4. 寫入 .mr_info.json 元資料
   ↓
5. 更新狀態資料庫
```

### 4.3 狀態管理

- **MRState**: 追蹤每個MR的狀態
- **ScanHistory**: 記錄掃描歷史
- **CloneInfo**: 儲存在 `.mr_info.json` 中

## 5. 異常處理

### 5.1 異常類型

- `ConfigError`: 設定錯誤
- `GitLabError`: GitLab API錯誤
- `CloneError`: Clone 操作錯誤
- `StateError`: 狀態管理錯誤
- `GitError`: Git操作錯誤

### 5.2 錯誤恢復

| 錯誤類型 | 處理方式 |
|---------|---------|
| GitLab連接失敗 | 重試3次，記錄錯誤，中止掃描 |
| MR資訊取得失敗 | 記錄錯誤，跳過該MR，繼續掃描 |
| Clone建立失敗 | 刪除殘留目錄，記錄日誌，繼續下一個MR |
| Git操作失敗 | 記錄錯誤，刪除目錄後重試一次 |

## 6. CLI 命令

### 6.1 scan 命令

掃描GitLab上的新MR並建立本地 clone。

```bash
python -m src.main scan [--dry-run]
```

**選項:**
- `--dry-run`: 試執行模式，不實際建立 clone

### 6.2 list-clones 命令

列出所有已建立的 MR clone 及其狀態。

```bash
python -m src.main list-clones
```

### 6.3 clean-clone 命令

清理指定的 MR clone。

```bash
python -m src.main clean-clone --iid <MR_IID> --project <PROJECT>
```

**選項:**
- `--iid`: MR的內部編號 (必需)
- `--project`: 專案路徑 (必需)

## 7. 設定管理

### 7.1 環境變數

所有設定選項可透過 `.env` 檔案進行設定。

**必要變數:**
- `GITLAB_URL`: GitLab執行個體URL
- `GITLAB_TOKEN`: GitLab存取令牌
- `GITLAB_PROJECTS`: 專案列表 (逗號分隔)

**可選變數:**
- `REVIEWS_PATH`: MR clone 根目錄 (預設: ~/GIT_POOL/reviews)
- `GITLAB_REPO_BASE`: GitLab 倉庫 base URL (預設: 從 GITLAB_URL 推導，用於 git clone)
- `STATE_DIR`: 狀態儲存目錄 (預設: ./state)
- `DB_PATH`: SQLite資料庫路徑 (預設: ./state/mr_state.sqlite)
- `LOG_LEVEL`: 日誌級別 (預設: INFO)

## 8. 日誌

### 8.1 日誌檔案

- 位置: `logs/` 目錄
- 格式: 時間戳、日誌級別、訊息
- 輪轉: 按大小輪轉

### 8.2 日誌級別

- `DEBUG`: 詳細的除錯訊息
- `INFO`: 一般訊息
- `WARNING`: 警告訊息
- `ERROR`: 錯誤訊息

## 9. 開發流程

### 9.1 TDD 流程

每個功能開發應遵循以下流程:

1. **Red**: 編寫失敗的測試案例
2. **Green**: 實現最小化的功能以通過測試
3. **Refactor**: 改進程式碼結構和質量

### 9.2 Commit 規範

使用conventional commit格式:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type:**
- `feat`: 新功能
- `fix`: 修正
- `test`: 測試案例
- `docs`: 文檔
- `refactor`: 重構
- `chore`: 雜務

詳見 [CONTRIBUTING.md](CONTRIBUTING.md)

## 10. 測試

### 10.1 測試框架

- pytest: 測試執行
- unittest.mock: Mock和Patch
- pytest-mock: Mock plugins

### 10.2 測試覆蓋

- Unit tests: 個別模組功能
- Integration tests: 模組間協作
- Error cases: 異常情況

## 11. 部署

### 11.1 安裝步驟

1. 複製專案
2. 安裝依賴: `pip install -r requirements.txt`
3. 設定環境變數: `cp .env.example .env && nano .env`
4. 驗證設定: `python -m src.main --help`

### 11.2 定期執行

使用 cron 定期執行掃描:

```bash
# 每小時執行一次
0 * * * * cd /path/to/gitlab_mr_reviewer && python -m src.main scan
```

## 12. 故障排除

### 12.1 常見問題

- **GitLab連接失敗**: 檢查URL和Token
- **Clone建立失敗**: 檢查磁碟空間、權限和網路連線
- **狀態載入失敗**: 檢查資料庫完整性

## 13. 性能考量

### 13.1 優化

- 快取GitLab回應
- 平行 clone 多個 MR（未來）
- 淺層 clone（`--depth 1`）可選支援

### 13.2 監控

- 掃描失敗次數
- API呼叫錯誤率
- Clone建立失敗
- 磁碟使用情況

## 14. 未來改進

- [ ] Web UI界面
- [ ] 支援其他 Git 服務
- [ ] 非同步操作
- [ ] 性能優化
- [ ] 擴展插件系統

---

版本: 0.1.0
最後更新: 2026-01-18
