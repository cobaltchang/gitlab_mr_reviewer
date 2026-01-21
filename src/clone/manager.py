"""
MR Clone 管理模組

使用 git clone --single-branch 策略為每個 MR 建立獨立的本地副本。
"""
import json
import logging
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..config import Config
from ..gitlab_.models import MRInfo
from ..state.manager import StateManager
from ..utils.exceptions import CloneError, GitError


logger = logging.getLogger(__name__)


class CloneManager:
    """MR Clone 管理器"""
    
    def __init__(self, config: Config, state_manager: StateManager):
        """
        初始化 Clone 管理器
        
        Args:
            config: 應用設定
            state_manager: 狀態管理器
        """
        self.config = config
        self.state_manager = state_manager
    
    def create_clone(self, mr_info: MRInfo) -> Path:
        """
        為 MR 建立 clone
        
        使用 git clone -b <source_branch> --single-branch 建立獨立副本。
        若目錄已存在則先刪除再重新 clone。
        
        Args:
            mr_info: MR 資訊
            
        Returns:
            clone 路徑
            
        Raises:
            CloneError: clone 建立失敗
        """
        try:
            clone_path = self._get_clone_path(mr_info)
            
            # 若目錄已存在，先刪除
            if clone_path.exists():
                logger.info(f"目錄已存在，刪除後重新 clone: {clone_path}")
                shutil.rmtree(clone_path)
            
            # 建立父目錄
            clone_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"建立 clone: {clone_path}")
            logger.debug(f"MR: {mr_info.project_name}#{mr_info.iid}")
            logger.debug(f"分支: {mr_info.source_branch}")
            
            # 建構 git clone 命令
            repo_url = self._get_repo_url(mr_info)
            clone_cmd = [
                'git',
                'clone',
                '-b', mr_info.source_branch,
                '--single-branch',
                repo_url,
                str(clone_path)
            ]
            
            logger.info(f"執行: {' '.join(clone_cmd)}")
            self._run_git_command(clone_cmd)
            
            # 確保目錄存在（git clone 會建立，但以防萬一）
            clone_path.mkdir(parents=True, exist_ok=True)
            
            # 保存元資料
            self._save_mr_metadata(mr_info, clone_path)
            
            # 更新狀態
            from src.state.models import MRState
            mr_state = MRState.from_mr_info(mr_info)
            self.state_manager.save_mr_state(mr_state)
            
            logger.info(f"Clone 建立成功: {clone_path}")
            return clone_path
        
        except GitError as e:
            # 清理可能的殘留目錄
            if clone_path.exists():
                shutil.rmtree(clone_path, ignore_errors=True)
            logger.error(f"建立 clone 失敗: {e}")
            raise CloneError(f"建立 clone 失敗: {e}")
        except Exception as e:
            if clone_path.exists():
                shutil.rmtree(clone_path, ignore_errors=True)
            logger.error(f"建立 clone 失敗: {e}")
            raise CloneError(f"建立 clone 失敗: {e}")
    
    def delete_clone(self, mr_info: MRInfo) -> bool:
        """
        刪除 MR clone
        
        Args:
            mr_info: MR 資訊
            
        Returns:
            是否刪除成功
        """
        try:
            clone_path = self._get_clone_path(mr_info)
            
            if not clone_path.exists():
                logger.warning(f"Clone 不存在: {clone_path}")
                return False
            
            logger.info(f"刪除 clone: {clone_path}")
            shutil.rmtree(clone_path)
            
            # 更新狀態
            self.state_manager.delete_mr_state(mr_info.id, mr_info.project_name)
            
            logger.info(f"Clone 刪除成功: {clone_path}")
            return True
        
        except Exception as e:
            logger.error(f"刪除 clone 失敗: {e}")
            return False
    
    def list_clones(self) -> Dict[str, List[int]]:
        """
        列出所有已建立的 clone
        
        Returns:
            專案 -> MR IID 列表的字典
        """
        result = {}
        reviews_path = Path(self.config.reviews_path).expanduser()
        
        if not reviews_path.exists():
            return result
        
        # 遍歷 reviews 目錄
        for project_dir in reviews_path.iterdir():
            if not project_dir.is_dir():
                continue
            
            # 處理 group/project 結構
            for sub_dir in project_dir.iterdir():
                if sub_dir.is_dir():
                    # 檢查是否為 MR IID 目錄（數字）
                    if sub_dir.name.isdigit():
                        # 單層專案結構: reviews/project/123
                        project_name = project_dir.name
                        if project_name not in result:
                            result[project_name] = []
                        result[project_name].append(int(sub_dir.name))
                    else:
                        # 雙層結構: reviews/group/project/123
                        for mr_dir in sub_dir.iterdir():
                            if mr_dir.is_dir() and mr_dir.name.isdigit():
                                project_name = f"{project_dir.name}/{sub_dir.name}"
                                if project_name not in result:
                                    result[project_name] = []
                                result[project_name].append(int(mr_dir.name))
        
        return result
    
    def get_clone_path(self, project: str, iid: int) -> Optional[Path]:
        """
        取得指定 MR 的 clone 路徑
        
        Args:
            project: 專案路徑
            iid: MR IID
            
        Returns:
            clone 路徑，若不存在則返回 None
        """
        clone_path = Path(self.config.reviews_path).expanduser() / project / str(iid)
        return clone_path if clone_path.exists() else None
    
    def _get_clone_path(self, mr_info: MRInfo) -> Path:
        """取得 clone 路徑"""
        return Path(self.config.reviews_path).expanduser() / mr_info.project_name / str(mr_info.iid)
    
    def _get_repo_url(self, mr_info: MRInfo) -> str:
        """
        取得 Git 倉庫 URL
        
        優先使用 config 中的 gitlab_repo_base，否則從 gitlab_url 推導
        """
        # 如果 config 有 gitlab_repo_base，使用它
        if hasattr(self.config, 'gitlab_repo_base') and self.config.gitlab_repo_base:
            return f"{self.config.gitlab_repo_base}{mr_info.project_name}.git"
        
        # 否則從 gitlab_url 推導（預設使用 SSH）
        # 例如: https://gitlab.example.com/ -> git@gitlab.example.com:
        gitlab_url = self.config.gitlab_url.rstrip('/')
        if gitlab_url.startswith('https://'):
            host = gitlab_url.replace('https://', '')
        elif gitlab_url.startswith('http://'):
            host = gitlab_url.replace('http://', '')
        else:
            host = gitlab_url
        
        return f"git@{host}:{mr_info.project_name}.git"
    
    def _save_mr_metadata(self, mr_info: MRInfo, clone_path: Path):
        """保存 MR 元資料"""
        metadata = {
            'mr_id': mr_info.id,
            'project_name': mr_info.project_name,
            'iid': mr_info.iid,
            'title': mr_info.title,
            'source_branch': mr_info.source_branch,
            'target_branch': mr_info.target_branch,
            'web_url': mr_info.web_url,
            'created_at': mr_info.created_at,
            'updated_at': mr_info.updated_at,
            'cloned_at': datetime.utcnow().isoformat(),
        }
        
        metadata_file = clone_path / '.mr_info.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    @staticmethod
    def _run_git_command(cmd, cwd=None):
        """執行 git 命令"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                cwd=cwd
            )
            
            if result.returncode != 0:
                raise GitError(f"Git 命令失敗: {result.stderr}")
            
            if result.stdout:
                logger.debug(f"Git 輸出: {result.stdout}")
                
            return result
        
        except GitError:
            raise
        except Exception as e:
            raise GitError(f"執行 git 命令失敗: {e}")


# 向後相容別名
WorktreeManager = CloneManager
