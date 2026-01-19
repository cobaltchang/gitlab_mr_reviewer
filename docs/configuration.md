# 設定说明

## 環境變數

所有設定選項可以透過 `.env` 檔案進行設定。參考 `.env.example` 取得完整的設定模板。

### GitLab连接設定

#### GITLAB_URL
GitLab 執行個體的 URL。

```bash
GITLAB_URL=https://ncs-gitlab/
```

#### GITLAB_TOKEN
GitLab 個人存取令牌。用於 API 认证。

```bash
GITLAB_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx
```

需要的權限范围：
- `api` - 完整 API 訪問
- `read_repository` - 读取仓库內容

生成方式：Settings → Personal Access Tokens

#### GITLAB_VERIFY_SSL
是否驗證 SSL 证书。預設 `true`。

```bash
GITLAB_VERIFY_SSL=true  # 生产環境应该为true
GITLAB_VERIFY_SSL=false # 開發環境或自签证书可设为false
```

### 本地路徑設定

#### REVIEWS_PATH
Worktree 的根目錄。所有 MR 對應的 worktree 将在此目錄下建立。

```bash
REVIEWS_PATH=~/GIT_POOL/reviews
```

worktree 目錄结构：
```
~/GIT_POOL/reviews/
├── group/project1/
│   ├── 1/        # MR#1 的 worktree
│   ├── 2/
│   └── 3/
└── group/project2/
    └── 45/
```

#### STATE_DIR
狀態檔案和資料库的存儲目錄。

```bash
STATE_DIR=~/.gitlab_mr_reviewer
```

#### DB_PATH
資料库檔案路徑。仅在 `STORAGE_TYPE=sqlite` 时使用。

```bash
DB_PATH=~/.gitlab_mr_reviewer/db.sqlite
```

### 監控專案設定

#### PROJECTS
要監控的專案列表，逗号分隔。支援專案 ID 或專案路徑。

```bash
# 使用專案ID
PROJECTS=123,456,789

# 使用專案路徑
PROJECTS=group/project1,group/project2,group/subgroup/project3

# 混合使用
PROJECTS=123,group/project1
```

### 掃描設定

#### SCAN_INTERVAL
掃描间隔，单位为秒。用於定时掃描。

```bash
SCAN_INTERVAL=3600  # 每小时掃描一次
SCAN_INTERVAL=1800  # 每30分钟掃描一次
```

#### EXCLUDE_WIP
是否排除 WIP（Work In Progress）标记的 MR。

```bash
EXCLUDE_WIP=true   # 排除WIP MR
EXCLUDE_WIP=false  # 包含WIP MR
```

#### EXCLUDE_DRAFT
是否排除草稿（Draft）MR。

```bash
EXCLUDE_DRAFT=true   # 排除草稿MR
EXCLUDE_DRAFT=false  # 包含草稿MR
```

#### MR_STATES
MR 狀態篩選。支援的值：`opened`, `merged`, `closed`, `locked`。

```bash
MR_STATES=opened                    # 只掃描打开的MR
MR_STATES=opened,merged             # 掃描打开和已合併的MR
MR_STATES=opened,merged,closed      # 掃描所有狀態的MR
```

### 日誌設定

#### LOG_LEVEL
日誌級別。可选值：`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`。

```bash
LOG_LEVEL=INFO      # 仅显示重要訊息
LOG_LEVEL=DEBUG     # 显示所有除錯訊息
```

#### LOG_FILE
日誌檔案路徑。如果不設定，仅输出到控制台。

```bash
LOG_FILE=~/.gitlab_mr_reviewer/scanner.log
```

#### LOG_MAX_SIZE
單個日誌檔案最大大小，單位為位元組。

```bash
LOG_MAX_SIZE=10485760  # 10MB
```

#### LOG_BACKUP_COUNT
保留的日誌檔案备份个数。

```bash
LOG_BACKUP_COUNT=5
```

### 存儲設定

#### STORAGE_TYPE
存儲后端类型。可选：`json` 或 `sqlite`。

```bash
STORAGE_TYPE=sqlite  # 推荐使用SQLite
STORAGE_TYPE=json    # 简单專案可使用JSON
```

**對比**：

| 特性 | SQLite | JSON |
|------|--------|------|
| 性能 | 好 | 一般 |
| 可扩展性 | 好 | 一般 |
| 查詢能力 | 强 | 弱 |
| 体积 | 小 | 较大 |
| 并发 | 支援 | 不支援 |

### 進階設定

#### DEBUG
啟用除錯模式。會輸出詳細的 API 請求和回應訊息。

```bash
DEBUG=true   # 启用除錯模式
DEBUG=false  # 禁用除錯模式
```

#### AUTO_CLEAN_MERGED
是否自動清理已合併 MR 的 worktree。

```bash
AUTO_CLEAN_MERGED=true   # 自動清理
AUTO_CLEAN_MERGED=false  # 保留已合併MR的worktree
```

#### CONNECTION_TIMEOUT
API 请求连接超时時間，单位为秒。

```bash
CONNECTION_TIMEOUT=30   # 30秒超时
```

#### API_RETRY_COUNT
API 請求重試次數。失敗時自動重試指定次數。

```bash
API_RETRY_COUNT=3   # 失敗後重試3次
```

## 設定檔案方式（可选）

除了環境變數，也可以使用 `config.yaml` 設定檔案：

```yaml
gitlab:
  url: https://ncs-gitlab/
  token: glpat-xxxxxxxxxxxxxxxxxxxx
  verify_ssl: true

scanning:
  projects:
    - group/project1
    - group/project2
  interval: 3600
  filters:
    exclude_wip: true
    exclude_draft: true
    mr_states:
      - opened

local:
  reviews_path: ~/GIT_POOL/reviews
  state_dir: ~/.gitlab_mr_reviewer
  storage_type: sqlite

logging:
  level: INFO
  file: ~/.gitlab_mr_reviewer/scanner.log
  max_size: 10485760
  backup_count: 5

advanced:
  debug: false
  auto_clean_merged: true
  connection_timeout: 30
  api_retry_count: 3
```

使用設定檔案執行：

```bash
python -m src.main scan --config config.yaml
```

## 設定驗證

在執行之前，可以驗證設定是否正确：

```bash
python -c "from src.config import Config; Config.from_env(); print('✓ 設定正确')"
```
