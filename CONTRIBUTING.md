"""
開發貢獻指南
"""

# GitLab MR Reviewer 開發指南

## 專案概述

GitLab MR Reviewer 是一個自動化的 Merge Request 審查工具，用於簡化開發團隊的代碼審查流程。

**技術棧：**
- Python 3.9+
- Click (CLI 框架)
- python-gitlab (GitLab API)
- GitPython (Git 操作)
- pytest (測試框架)

## 開發原則

本項目遵循以下開發原則：

### 1. 測試驅動開發 (TDD)


### 測試覆蓋率要求

本專案維持嚴格的覆蓋率政策以確保核心邏輯的健全性。

- 覆蓋範圍: `src` 目錄（已在 `.coveragerc` 中排除已棄用的 `src/worktree/`）
- 目標: **100%**（所有受測模組在 `src` 中皆達到覆蓋）
- 新增或修改程式碼時，必須同時新增/更新測試以維持此標準

驗證命令（本機）:
```bash
# 生成終端覆蓋率摘要
pytest tests/ --cov=src --cov-report=term-missing --timeout=10

# 生成 HTML 覆蓋率報告（可在瀏覽器打開）
pytest tests/ --cov=src --cov-report=html --timeout=10
open htmlcov/index.html
```

實務與例外:
- 已棄用或遺留模組 （例如 `src/worktree/`）可在 `.coveragerc` 中列為 omit；omit 必須在 PR 中說明理由。
- 防禦性極罕見的分支（例如用於清理殘留檔案的 `ignore_errors=True` 路徑）若測試成本過高，可納入討論並由核心維護者決定是否以 `# pragma: no cover` 或其他方式排除。
- CI 構建應設定最低覆蓋率門檻（建議 `100%`），或至少在 PR 審查時明確標註任何減低覆蓋率的變更。
所有功能開發必須遵循 Red → Green → Refactor 流程：

1. **Red**: 編寫失敗的單元測試
2. **Green**: 實現最小化程式碼使測試通過
3. **Refactor**: 改進程式碼質量和可讀性

### 2. 模塊化架構

項目採用嚴格的模塊化設計：

```
src/
├── config.py                # 應用設定
├── logger/                  # 日誌系統
├── utils/                   # 通用工具和異常
├── gitlab_/                 # GitLab API 集成
├── scanner/                 # MR 掃描引擎
├── state/                   # 狀態持久化
├── clone/                   # MR Clone 管理
└── main.py                  # CLI 主應用
```

每個模塊應該：
- 職責單一
- 依賴最少化
- 提供清晰的公開 API
- 包含完整的單元測試

### 3. 異常處理

使用自定義異常進行錯誤管理：

```python
from src.utils.exceptions import (
    ConfigError,      # 設定錯誤
    GitLabError,      # GitLab API 錯誤
    CloneError,       # Clone 操作錯誤
    StateError,       # 狀態管理錯誤
    GitError          # Git 操作錯誤
)
```

### 4. 日誌記錄

使用中央日誌系統記錄所有重要事件：

```python
from src.logger import logger

logger.info("應用啟動")
logger.error("發生錯誤", exc_info=True)
```

## 開發流程

### 設定開發環境

1. **克隆專案**
```bash
git clone <repo_url>
cd gitlab_mr_reviewer
```

2. **建立虛擬環境**
```bash
python3.9 -m venv venv
source venv/bin/activate
```

3. **安裝依賴**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 開發依賴
```

4. **設定環境變數**
```bash
cp .env.example .env
# 編輯 .env 填入實際的 GitLab 信息
```

### 實現新功能

假設要添加新的「產生審查報告」功能：

#### Step 1: 編寫測試

```python
# tests/test_report.py
import pytest
from src.report.generator import ReportGenerator

class TestReportGenerator:
    def test_generate_report_success(self):
        """測試成功產生報告"""
        generator = ReportGenerator()
        report = generator.generate()
        
        assert report is not None
        assert report.title == "MR 審查報告"
```

#### Step 2: 運行測試（應該失敗）

```bash
pytest tests/test_report.py -v
# FAILED - ModuleNotFoundError: No module named 'src.report'
```

#### Step 3: 實現功能

```python
# src/report/generator.py
from dataclasses import dataclass

@dataclass
class Report:
    title: str
    content: str

class ReportGenerator:
    def generate(self) -> Report:
        """產生審查報告"""
        return Report(
            title="MR 審查報告",
            content="報告內容"
        )
```

#### Step 4: 運行測試（應該通過）

```bash
pytest tests/test_report.py -v
# PASSED
```

#### Step 5: 重構和優化

改進程式碼質量、添加文檔等。

#### Step 6: 提交變更

```bash
git add src/report/ tests/test_report.py
git commit -m "feat(report): 實現 MR 審查報告產生功能"
```

## 代碼風格

### 命名約定

- **模塊和檔案**: snake_case (例: `mr_scanner.py`)
- **類別**: PascalCase (例: `MRScanner`)
- **函數和變數**: snake_case (例: `get_merge_requests()`)
- **常數**: UPPER_SNAKE_CASE (例: `MAX_RETRIES = 3`)

### 文檔字符串

所有公開類別和函數必須有詳細的文檔字符串：

```python
def create_clone(self, mr_info: MRInfo) -> Path:
    """
    為 MR 建立 clone
    
    Args:
        mr_info: MR 訊息
        
    Returns:
        Clone 路徑
        
    Raises:
        CloneError: 建立失敗
    """
```

### 類型提示

所有函數必須使用類型提示：

```python
from typing import Optional, List
from src.gitlab_.models import MRInfo

def scan(
    self,
    projects: List[str],
    exclude_wip: bool = False,
    exclude_draft: bool = False
) -> List['ScanResult']:
    """掃描 MR"""
```

## 測試

### 運行測試

```bash
# 運行所有測試
pytest tests/ -v

# 運行特定測試檔案
pytest tests/test_config.py -v

# 運行特定測試
pytest tests/test_config.py::TestConfig::test_config_from_env -v

# 查看代碼覆蓋率
pytest tests/ --cov=src --cov-report=html
```

### 編寫測試

測試應該：

1. **命名清晰**: `test_<function>_<scenario>`
   ```python
   def test_create_clone_success(self):
   def test_create_clone_already_exists(self):
   ```

2. **使用 Fixtures**: 集中管理測試資源
   ```python
   @pytest.fixture
   def mr_info():
       return MRInfo(...)
   ```

3. **使用 Mock**: 隔離外部依賴
   ```python
   from unittest.mock import patch, MagicMock
   
   @patch('src.gitlab_.client.GitLabClient')
   def test_scan(self, mock_client):
       mock_client.return_value.get_mr.return_value = mr_info
   ```

4. **覆蓋邊界情況**:
   - 成功路徑
   - 失敗路徑
   - 邊界條件
   - 異常情況

## Git 工作流

### 分支策略

本項目使用簡化的 Git 工作流：

1. **main**: 穩定發佈版本
2. **feature/***: 新功能分支
3. **bugfix/***: 缺陷修復分支

### Commit 消息格式

遵循 Conventional Commits 規範：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: 新功能
- `fix`: 缺陷修復
- `docs`: 文檔更新
- `test`: 測試添加或修改
- `refactor`: 代碼重構
- `style`: 代碼風格修改
- `chore`: 構建系統或依賴變更

**Examples:**

```
feat(clone): 實現 MR Clone 管理

- 支援建立、更新、刪除 clone
- 整合 StateManager 追蹤狀態
- 完整的錯誤處理

Closes #42
```

```
fix(gitlab_client): 修復 SSL 驗證問題

當 GITLAB_SSL_VERIFY=false 時，應跳過 SSL 驗證。
之前的實現未正確傳遞此參數。
```

## 質量保證

### 檢查清單

在提交前，確保：

- [ ] 所有新功能都有對應的單元測試
- [ ] 所有測試都通過: `pytest tests/ -v`
- [ ] 代碼風格符合規範: `pylint src/`
- [ ] 沒有未使用的 import: `autoflake --check src/`
- [ ] 所有文檔字符串都存在
- [ ] commit 消息清晰有意義

### 持續集成

每次提交會自動運行：

1. **Linting**: 代碼風格檢查
2. **Testing**: 單元測試
3. **Coverage**: 代碼覆蓋率檢查

所有檢查必須通過才能合併。

## 常見開發任務

### 添加新的 CLI 命令

1. 在 `src/main.py` 中添加新的 `@cli.command()`
2. 在 `tests/test_main.py` 中添加測試
3. 更新 `spec.md` 中的命令文檔

### 添加新的異常類型

1. 在 `src/utils/exceptions.py` 中添加新異常
2. 在 `tests/test_exceptions.py` 中添加測試
3. 在相應模塊中使用新異常

### 更新 GitLab API 集成

1. 在 `src/gitlab_/models.py` 中更新資料模型
2. 在 `src/gitlab_/client.py` 中添加新方法
3. 在 `tests/test_gitlab_client.py` 中添加測試

## 疑難排解

### 測試失敗

```bash
# 查看詳細的失敗信息
pytest tests/test_xxx.py -v --tb=long

# 進入調試器
pytest tests/test_xxx.py -v --pdb
```

### 導入錯誤

確保在虛擬環境中安裝了所有依賴：

```bash
pip install -r requirements.txt
```

### 環境變數未設定

確保 `.env` 檔案存在且包含所有必要的變數：

```bash
cp .env.example .env
# 編輯 .env
```

## 貢獻指南

感謝您的貢獻！請遵循以下步驟：

1. Fork 本專案
2. 建立特性分支: `git checkout -b feature/amazing-feature`
3. Commit 變更: `git commit -m 'feat: Add amazing feature'`
4. Push 到分支: `git push origin feature/amazing-feature`
5. 提交 Pull Request

## 聯繫方式

如有問題或建議，請提交 Issue 或 Pull Request。

---

**最後更新:** 2026-01-19
**版本:** 1.0.0
