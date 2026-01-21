# 使用指南

本檔說明 CLI 用法與常見範例。

## 基本命令

### 掃描 MR 並建立 clone

```bash
python -m src.main scan
```

### 列出所有已建立的 MR clone

```bash
python -m src.main list-clones
```

### 刪除特定 MR clone

```bash
python -m src.main clean-clone --iid 123 --project group/project
```

## 掃描選項

### 排除 WIP 和草稿 MR

```bash
# 排除 WIP (Work In Progress) MR
python -m src.main scan --exclude-wip

# 排除草稿 (Draft) MR
python -m src.main scan --exclude-draft

# 同時排除 WIP 和草稿
python -m src.main scan --exclude-wip --exclude-draft
```

### 試執行模式

不會實際建立或刪除：

```bash
python -m src.main scan --dry-run
```

## 進階用法

結合環境變數配置與 `GITLAB_PROJECTS_FILE`，例如在 CI 或排程中執行：

```bash
# 載入 .env
export $(cat .env | grep -v '#' | xargs)

# 執行一次掃描
python -m src.main scan --dry-run
```

## 目錄結構

執行 scan 後，MR clone 會建立在 `REVIEWS_PATH` 下：

```
~/GIT_POOL/reviews/
├── group/project1/
│   ├── 42/           # MR #42 的 clone
│   │   ├── .mr_info.json
│   │   └── (專案檔案)
│   └── 123/          # MR #123 的 clone
└── group/project2/
    └── 7/
```

每個 MR clone 都是獨立的 git repository（single-branch 模式），包含該 MR 的 source branch。
