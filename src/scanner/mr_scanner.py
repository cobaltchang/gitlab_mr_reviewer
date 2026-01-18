"""
MR 掃描和篩選引擎
"""

from dataclasses import dataclass
from typing import List

from src.gitlab_.client import GitLabClient
from src.gitlab_.models import MRInfo
from src.logger import logger


@dataclass
class ScanResult:
    """掃描結果"""
    project: str
    merge_requests: List[MRInfo]
    error: str = None


class MRScanner:
    """MR 掃描器"""
    
    def __init__(self, client: GitLabClient, state_manager):
        """
        初始化掃描器
        
        Args:
            client: GitLab 客戶端
            state_manager: 狀態管理器
        """
        self.client = client
        self.state_manager = state_manager
    
    def scan(self, projects: List[str], exclude_wip: bool = True, exclude_draft: bool = True) -> List[ScanResult]:
        """
        掃描指定專案的 MR
        
        Args:
            projects: 專案列表
            exclude_wip: 排除 WIP MR
            exclude_draft: 排除草稿 MR
            
        Returns:
            ScanResult 列表
        """
        results = []
        
        for project in projects:
            try:
                # 取得當前的 MR 列表
                logger.info(f"掃描專案: {project}")
                mrs = self.client.get_merge_requests(project)
                
                # 篩選 MR
                filtered_mrs = self._filter_mrs(mrs, exclude_wip=exclude_wip, exclude_draft=exclude_draft)
                
                logger.info(f"專案 {project} 有 {len(filtered_mrs)} 個符合條件的 MR")
                
                results.append(ScanResult(
                    project=project,
                    merge_requests=filtered_mrs,
                    error=None
                ))
            except Exception as e:
                logger.error(f"掃描專案 {project} 失敗: {e}")
                results.append(ScanResult(
                    project=project,
                    merge_requests=[],
                    error=str(e)
                ))
        
        return results
    
    def _filter_mrs(self, mrs: List[MRInfo], exclude_wip: bool = True, exclude_draft: bool = True) -> List[MRInfo]:
        """
        篩選 MR 列表
        
        Args:
            mrs: MR 列表
            exclude_wip: 排除 WIP MR
            exclude_draft: 排除草稿 MR
            
        Returns:
            篩選後的 MR 列表
        """
        filtered = []
        
        for mr in mrs:
            # 檢查是否應該排除
            if exclude_wip and mr.work_in_progress:
                logger.debug(f"排除 WIP MR: {mr.iid}")
                continue
            
            if exclude_draft and mr.draft:
                logger.debug(f"排除草稿 MR: {mr.iid}")
                continue
            
            filtered.append(mr)
        
        return filtered
