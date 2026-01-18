"""
GitLab API 客戶端模組
"""

from typing import List, Any

import gitlab

from src.gitlab_.models import MRInfo, Change, Commit
from src.logger import logger
from src.utils.exceptions import GitLabError


class GitLabClient:
    """GitLab API 客戶端"""
    
    def __init__(self, url: str, token: str, ssl_verify: bool = True):
        """
        初始化 GitLab 客戶端
        
        Args:
            url: GitLab 執行個體 URL
            token: GitLab 存取令牌
            ssl_verify: 是否驗證 SSL 憑證
        """
        try:
            self.gl = gitlab.Gitlab(url, private_token=token, ssl_verify=ssl_verify)
            self.gl.auth()
            logger.info(f"成功連接到 GitLab: {url}")
        except Exception as e:
            logger.error(f"連接 GitLab 失敗: {e}")
            raise GitLabError(f"連接 GitLab 失敗: {e}")
    
    def get_project(self, project_id: str) -> Any:
        """
        取得專案對象
        
        Args:
            project_id: 專案 ID 或路徑
            
        Returns:
            gitlab Project 對象
            
        Raises:
            GitLabError: 無法取得專案
        """
        try:
            project = self.gl.projects.get(project_id)
            return project
        except Exception as e:
            logger.error(f"取得專案失敗: {e}")
            raise GitLabError(f"取得專案失敗: {e}")
    
    def get_merge_requests(self, project_id: str) -> List[MRInfo]:
        """
        取得專案的 MR 列表
        
        Args:
            project_id: 專案 ID 或路徑
            
        Returns:
            MRInfo 對象列表
            
        Raises:
            GitLabError: 無法取得 MR 列表
        """
        try:
            project = self.get_project(project_id)
            mrs = project.mergerequests.list(all=True, state="opened")
            
            results = []
            for mr in mrs:
                results.append(self._convert_mr_to_info(mr, project))
            
            logger.debug(f"取得專案 {project_id} 的 {len(results)} 個 MR")
            return results
        except GitLabError:
            raise
        except Exception as e:
            logger.error(f"取得 MR 列表失敗: {e}")
            raise GitLabError(f"取得 MR 列表失敗: {e}")
    
    def get_mr_details(self, project_id: str, mr_iid: int) -> MRInfo:
        """
        取得單個 MR 的詳細訊息
        
        Args:
            project_id: 專案 ID 或路徑
            mr_iid: MR 的專案內編號
            
        Returns:
            MRInfo 對象
            
        Raises:
            GitLabError: 無法取得 MR 詳情
        """
        try:
            project = self.get_project(project_id)
            mr = project.mergerequests.get(mr_iid)
            return self._convert_mr_to_info(mr, project)
        except GitLabError:
            raise
        except Exception as e:
            logger.error(f"取得 MR 詳情失敗: {e}")
            raise GitLabError(f"取得 MR 詳情失敗: {e}")
    
    def get_mr_changes(self, project_id: str, mr_iid: int) -> List[Change]:
        """
        取得 MR 的變更列表
        
        Args:
            project_id: 專案 ID 或路徑
            mr_iid: MR 的專案內編號
            
        Returns:
            Change 對象列表
            
        Raises:
            GitLabError: 無法取得 MR 變更
        """
        try:
            project = self.get_project(project_id)
            mr = project.mergerequests.get(mr_iid)
            changes = mr.changes()
            
            results = []
            for change in changes.get("changes", []):
                results.append(Change(
                    old_path=change.get("old_path"),
                    new_path=change.get("new_path"),
                    new_file=change.get("new_file", False),
                    deleted_file=change.get("deleted_file", False),
                    renamed_file=change.get("renamed_file", False),
                ))
            
            return results
        except GitLabError:
            raise
        except Exception as e:
            logger.error(f"取得 MR 變更失敗: {e}")
            raise GitLabError(f"取得 MR 變更失敗: {e}")
    
    def get_mr_commits(self, project_id: str, mr_iid: int) -> List[Commit]:
        """
        取得 MR 的提交列表
        
        Args:
            project_id: 專案 ID 或路徑
            mr_iid: MR 的專案內編號
            
        Returns:
            Commit 對象列表
            
        Raises:
            GitLabError: 無法取得 MR 提交列表
        """
        try:
            project = self.get_project(project_id)
            mr = project.mergerequests.get(mr_iid)
            commits = mr.commits()
            
            results = []
            for commit in commits:
                results.append(Commit(
                    id=commit.id,
                    short_id=commit.short_id,
                    title=commit.title,
                    message=commit.message,
                    author_name=commit.author_name,
                    author_email=commit.author_email,
                    created_at=commit.created_at,
                ))
            
            return results
        except GitLabError:
            raise
        except Exception as e:
            logger.error(f"取得 MR 提交列表失敗: {e}")
            raise GitLabError(f"取得 MR 提交列表失敗: {e}")
    
    @staticmethod
    def _convert_mr_to_info(mr, project) -> MRInfo:
        """
        將 GitLab MR 對象轉換為 MRInfo
        """
        return MRInfo(
            id=mr.id,
            project_id=project.id,
            project_name=project.path_with_namespace,
            iid=mr.iid,
            title=mr.title,
            description=mr.description or "",
            state=mr.state,
            author=mr.author.get("username", "unknown") if mr.author else "unknown",
            created_at=mr.created_at,
            updated_at=mr.updated_at,
            source_branch=mr.source_branch,
            target_branch=mr.target_branch,
            web_url=mr.web_url,
            draft=mr.draft or False,
            work_in_progress=mr.work_in_progress or False,
        )
