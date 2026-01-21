````markdown
# 使用指南

本檔說明 CLI 用法與常見範例。

### 基本命令

掃描 MR 並建立或更新 worktree：

```bash
python -m src.main scan
```

列出所有已建立的 worktree：

```bash
python -m src.main list-worktrees
```

刪除特定 worktree：

```bash
python -m src.main clean-worktree --iid 123 --project group/project
```

試執行模式（不會實際建立或刪除）：

```bash
python -m src.main scan --dry-run
```

更複雜的使用示例可結合環境變數配置與 `GITLAB_PROJECTS_FILE`，例如在 CI 或排程中執行：

```bash
# 載入 .env
export $(cat .env | grep -v '#' | xargs)

# 執行一次掃描
python -m src.main scan --dry-run
```

````
