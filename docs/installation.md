# 安裝指南

## 前提條件

- Python 3.11 或更高版本
- pip 或 poetry
- Git 2.30 或更高版本
- GitLab 執行個體存取權限

## 安裝步驟

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

### 3. 安裝依賴

```bash
pip install -r requirements.txt
```

### 4. 設定環境變數和專案清單

#### 4.1 複製環境變數範本

```bash
# 複製示例設定檔案
cp .env.example .env

# 編輯 .env 檔案，設定以下必要參數：
# - GITLAB_URL: GitLab 執行個體 URL
# - GITLAB_TOKEN: 個人存取令牌
# - GITLAB_PROJECTS_FILE: 專案清單檔案路徑（推薦）
nano .env

# 將 .env 變數載入到環境中（每次開啟新終端都需要執行）
export $(cat .env | grep -v '#' | xargs)
```

#### 4.2 建立專案清單檔案

```bash
# 複製範例檔案
cp gitlab_projects.txt.example gitlab_projects.txt

# 編輯檔案，每行一個專案
nano gitlab_projects.txt
```

專案清單檔案 (`gitlab_projects.txt`) 格式：
```
# 註釋行以 # 開頭，會被忽略
# 空行也會被忽略

group/project1
group/project2
group/subgroup/project3
```

### 5. 生成 GitLab 個人存取令牌

1. 訪問 GitLab 執行個體: https://ncs-gitlab/
2. 登入到你的帳戶
3. 點擊右上角頭像 → Settings
4. 左邊欄點擊 Access Tokens
5. 建立新令牌，需要的權限：
   - `api` - 完整 API 訪問
   - `read_repository` - 讀取倉庫內容
6. 複製生成的令牌到 `.env` 檔案中的 `GITLAB_TOKEN`

### 6. 驗證安裝

```bash
python -m src.main --help
```

如果看到幫助訊息，說明安裝成功。

## 快速開始

```bash
# 首次掃描
python -m src.main scan

# 列出所有 worktrees
python -m src.main list-worktrees

# 刪除特定 worktree
python -m src.main clean-worktree <project_path> <mr_number>
```

## 故障排除

### 無法連接至 GitLab

- 檢查 `GITLAB_URL` 是否正確
- 檢查網路連接
- 驗證 GitLab 執行個體是否可訪問

### 令牌無效

- 檢查 `GITLAB_TOKEN` 是否複製正確
- 檢查令牌是否過期（GitLab 可設定令牌有效期）
- 檢查令牌權限是否足夠

### Worktree 建立失敗

- 檢查 `REVIEWS_PATH` 目錄是否有寫權限
- 檢查磁碟空間是否充足
- 檢查源倉庫是否存在

### 權限錯誤

- 檢查專案是否有權限訪問
- 檢查目錄權限（`chmod u+rwx`）
