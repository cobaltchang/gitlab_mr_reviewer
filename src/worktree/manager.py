"""
Worktree管理模組
"""
import logging
import subprocess
from pathlib import Path
from typing import Optional

from ..config import Config
from ..gitlab_.models import MRInfo
from ..state.manager import StateManager
from ..utils.exceptions import WorktreeError, GitError


logger = logging.getLogger(__name__)


class WorktreeManager:
    """Git worktree管理器"""
    
    def __init__(self, config: Config, state_manager: StateManager):
        """
        初始化worktree管理器
        
        Args:
            config: 應用設定
            state_manager: 狀態管理器
        """
        self.config = config
        self.state_manager = state_manager
    
    def create_worktree(self, mr_info: MRInfo) -> Path:
        """
        为MR建立worktree
        
        Args:
            mr_info: MR訊息
            
        Returns:
            worktree路徑
        """
        try:
            worktree_path = self._get_worktree_path(mr_info)
            
            # 檢查worktree是否已存在
            if worktree_path.exists():
                logger.warning(f"Worktree已存在: {worktree_path}")
                self.update_worktree(mr_info)
                return worktree_path
            
            # 建立父目錄
            worktree_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"建立worktree: {worktree_path}")
            logger.debug(f"MR: {mr_info.project_name}#{mr_info.iid}")
            logger.debug(f"分支: origin/{mr_info.source_branch}")

            # 1. 先把該 MR 的特定 Ref 抓下來
            # refs/merge-requests/{iid}/head 是 GitLab 官方提供的虛擬引用
            git_repo_path = self._get_git_repo_path(mr_info)
            fetch_cmd = [
               'git',
               'fetch',
               'origin',
                f'refs/merge-requests/{mr_info.iid}/head'
            ]
            
            logger.info(f"Fetching MR !{mr_info.iid}...")
            self._run_git_command(fetch_cmd, cwd=git_repo_path)

            # 2. 從抓下來的快取 (FETCH_HEAD) 建立 worktree
            # 使用git worktree add命令
            # 需要確保有一個本地倉庫的複製
            add_cmd = [
                'git',
                'worktree',
                'add',
                str(worktree_path),
                'FETCH_HEAD'
            ]
            
            self._run_git_command(add_cmd, cwd=git_repo_path)
            
            # 保存元数据
            self._save_mr_metadata(mr_info, worktree_path)
            
            # 更新狀態
            from src.state.models import MRState
            mr_state = MRState.from_mr_info(mr_info)
            self.state_manager.save_mr_state(mr_state)
            
            logger.info(f"Worktree建立成功: {worktree_path}")
            return worktree_path
        
        except Exception as e:
            logger.error(f"建立worktree失敗: {e}")
            raise WorktreeError(f"建立worktree失敗: {e}")
    
    def update_worktree(self, mr_info: MRInfo) -> bool:
        """
        更新worktree内容
        
        Args:
            mr_info: MR訊息
            
        Returns:
            是否有更新
        """
        try:
            worktree_path = self._get_worktree_path(mr_info)
            
            # 檢查worktree是否存在
            if not worktree_path.exists():
                logger.warning(f"Worktree不存在: {worktree_path}")
                return False
            
            logger.info(f"更新worktree: {worktree_path}")
            
            # 取得當前HEAD
            current_sha = self._get_current_sha(worktree_path)
            
            # 檢查是否有本地修改
            if self._has_local_changes(worktree_path):
                logger.warning(f"Worktree有本地修改，跳过更新: {worktree_path}")
                return False
            
            # 注意：無法比較 head_commit_sha，因為 MRInfo 中沒有此欄位
            # 改為強制更新
            
            # 執行git pull更新
            logger.debug(f"執行git pull更新MR !{mr_info.iid}")

            # 可能有 force update，先回到原本的點
            cmd = ['git', '-C', str(worktree_path), 'reset', '--hard', mr_info.target_branch]
            self._run_git_command(cmd)

            # 拉新的 code 下來
            cmd = ['git', '-C', str(worktree_path), 'pull', 'origin', f'refs/merge-requests/{mr_info.iid}/head']
            self._run_git_command(cmd)
            
            # 更新元数据
            self._save_mr_metadata(mr_info, worktree_path)
            
            # 更新狀態
            from src.state.models import MRState
            mr_state = MRState.from_mr_info(mr_info)
            self.state_manager.save_mr_state(mr_state)
            
            logger.info(f"Worktree更新成功: {worktree_path}")
            return True
        
        except Exception as e:
            logger.error(f"更新worktree失敗: {e}")
            return False
    
    def delete_worktree(self, mr_info: MRInfo) -> bool:
        """
        刪除worktree
        
        Args:
            mr_info: MR訊息
            
        Returns:
            是否刪除成功
        """
        try:
            worktree_path = self._get_worktree_path(mr_info)
            
            if not worktree_path.exists():
                logger.warning(f"Worktree不存在: {worktree_path}")
                return False
            
            logger.info(f"刪除worktree: {worktree_path}")
            
            # 使用git worktree remove命令
            cmd = ['git', 'worktree', 'remove', str(worktree_path)]
            self._run_git_command(cmd, cwd=str(worktree_path.parent.parent))
            
            # 清理目錄
            if worktree_path.exists():
                import shutil
                shutil.rmtree(worktree_path)
            
            # 更新狀態
            self.state_manager.delete_mr_state(mr_info.id, mr_info.project_name)
            
            logger.info(f"Worktree刪除成功: {worktree_path}")
            return True
        
        except Exception as e:
            logger.error(f"刪除worktree失敗: {e}")
            return False
    
    def _get_git_repo_path(self, mr_info: MRInfo) -> Path:
        """
        取得 Git 倉庫路徑
        
        reviews_path 用於存放 worktrees，而主倉庫位於 reviews_path 的上層目錄
        結構如下：
        - ~/GIT_POOL/                     (主倉庫所在層)
        - ~/GIT_POOL/project_name/.git    (實際的 git 倉庫)
        - ~/GIT_POOL/reviews/             (worktrees 根目錄)
        - ~/GIT_POOL/reviews/project_name/1/ (worktree)
        - ~/GIT_POOL/reviews/project_name/2/ (worktree)
        """
        return Path(self.config.reviews_path).expanduser().parent / mr_info.project_name

    def _get_worktree_path(self, mr_info: MRInfo) -> Path:
        """取得worktree路徑"""
        return Path(self.config.reviews_path).expanduser() / mr_info.project_name / str(mr_info.iid)
    
    def _save_mr_metadata(self, mr_info: MRInfo, worktree_path: Path):
        """保存MR元数据"""
        import json
        from datetime import datetime
        
        # 確保目錄存在
        worktree_path.mkdir(parents=True, exist_ok=True)
        
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
            'saved_at': datetime.utcnow().isoformat(),
        }
        
        metadata_file = worktree_path / '.mr_info.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    @staticmethod
    def _get_current_sha(worktree_path: Path) -> Optional[str]:
        """取得當前worktree的HEAD SHA"""
        try:
            cmd = ['git', '-C', str(worktree_path), 'rev-parse', 'HEAD']
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except Exception as e:
            logger.error(f"取得HEAD SHA失敗: {e}")
            return None
    
    @staticmethod
    def _has_local_changes(worktree_path: Path) -> bool:
        """
        檢查 worktree 是否有本地修改
        
        忽略 .mr_info.json 這個自動生成的文件
        """
        try:
            cmd = ['git', '-C', str(worktree_path), 'status', '--porcelain']
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # 過濾出非 .mr_info.json 的變更
            changes = [line for line in result.stdout.strip().split('\n') 
                      if line and not line.endswith('.mr_info.json')]
            
            return bool(changes)
        except Exception:
            return True  # 如果無法檢查，認為有修改
    
    @staticmethod
    def _run_git_command(cmd, cwd=None):
        """執行git命令"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                cwd=cwd
            )
            
            if result.returncode != 0:
                raise GitError(f"Git命令失敗: {result.stderr}")
            
            if result.stdout:
                logger.debug(f"Git 輸出: {result.stdout}")
        
        except Exception as e:
            raise GitError(f"執行git命令失敗: {e}")
