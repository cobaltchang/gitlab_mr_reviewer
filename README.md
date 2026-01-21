# GitLab MR Reviewer

自動化 GitLab MR 掃描與本地審查工具。定期掃描 https://gitlab.example.com/ 上的新 Merge Requests，自動在本地建立 git worktrees，支援增量更新，便於程式碼審查。

## 功能特性

- 🔍 **MR 掃描**：自動掃描 GitLab 上符合條件的 Merge Requests
- 📂 **Worktree 管理**：自動建立和管理本地 git worktree 用於審查
- 🔄 **增量更新**：支援增量掃描和狀態追蹤
- 💾 **狀態持久化**：SQLite 和 JSON 雙存儲支援
- 📝 **完整日誌**：記錄所有操作和錯誤訊息
- 🛠️ **CLI 工具**：簡單易用的命令行界面

## 快速開始

### 安裝

```bash
# 複製項目
git clone <repository_url>
cd gitlab_mr_reviewer

# 安裝依賴
pip install -r requirements.txt
```

### 設定

```bash
# 複製環境變數範本
cp .env.example .env

# 編輯 .env 檔案，設定您的 GitLab 連接訊息
```

### 使用

```bash
# 掃描 MR 並建立 worktree
python -m src.main scan

# 列出所有已建立的 worktree
python -m src.main list-worktrees

# 清理指定的 worktree
python -m src.main clean-worktree --iid <MR_IID>

# 試執行模式
python -m src.main scan --dry-run
```

## 開發

本項目遵循 TDD (Test-Driven Development) 方法論。每個 commit 都應包含對應的測試，並確保所有測試通過。

詳見 [CONTRIBUTING.md](CONTRIBUTING.md) 瞭解開發流程和規範。

## 文檔

- [安裝和設定](docs/installation.md)
- [配置選項](docs/configuration.md)
- [使用指南](docs/usage.md)
- [開發貢獻指南](CONTRIBUTING.md)
- [項目規範](spec.md)

## 測試

```bash
# 運行所有測試
pytest

# 運行特定測試
pytest tests/test_config.py

# 查看覆蓋率
pytest --cov=src
```

## 許可證

MIT
