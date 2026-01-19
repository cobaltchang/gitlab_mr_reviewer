# 安装指南

## 前提條件

- Python 3.11 或更高版本
- pip 或 poetry
- Git 2.30 或更高版本
- GitLab 執行個體存取權限

## 安装步骤

### 1. 複製專案

```bash
git clone <repository_url>
cd gitlab_mr_reviewer
```

### 2. 建立虛擬環境

```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 設定環境變數

```bash
# 複製示例設定檔案
cp .env.example .env

# 編輯.env檔案，設定以下必要參數：
# - GITLAB_URL: GitLab執行個體URL
# - GITLAB_TOKEN: 個人存取令牌
# - GITLAB_PROJECTS: 要監控的專案列表
nano .env

# 將 .env 變數載入到環境中（每次開啟新終端都需要執行）
export $(cat .env | grep -v '#' | xargs)
```

### 5. 生成GitLab個人存取令牌

1. 訪問 GitLab 執行個體: https://ncs-gitlab/
2. 登录到你的账户
3. 点击右上角头像 → Settings
4. 左边栏点击 Access Tokens
5. 建立新令牌，需要的權限：
   - `api` - 完整 API 訪問
   - `read_repository` - 读取仓库內容
6. 複製生成的令牌到 `.env` 檔案中的 `GITLAB_TOKEN`

### 6. 驗證安装

```bash
python -m src.main --help
```

如果看到帮助訊息，说明安装成功。

## 快速开始

```bash
# 首次掃描
python -m src.main scan

# 列出所有worktrees
python -m src.main list-worktrees

# 刪除specific worktree
python -m src.main clean-worktree <project_path> <mr_number>
```

## 故障排除

### 无法連接至GitLab

- 檢查 `GITLAB_URL` 是否正确
- 檢查网络连接
- 驗證 GitLab 執行個體是否可訪問

### 令牌无效

- 檢查 `GITLAB_TOKEN` 是否複製正确
- 檢查令牌是否过期（GitLab 可設定令牌有效期）
- 檢查令牌權限是否足够

### Worktree建立失敗

- 檢查 `REVIEWS_PATH` 目錄是否有写權限
- 檢查磁盘空间是否充足
- 檢查源仓库是否存在

### 權限錯誤

- 檢查專案是否有權限訪問
- 檢查目錄權限（`chmod u+rwx`）
