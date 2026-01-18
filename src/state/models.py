"""
狀態資料模型
"""

from dataclasses import dataclass, field
from datetime import datetime

from src.gitlab_.models import MRInfo


@dataclass
class MRState:
    """MR 狀態"""
    mr_id: int
    project_slug: str
    iid: int
    state: str
    head_commit_sha: str
    saved_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @classmethod
    def from_mr_info(cls, mr_info: MRInfo) -> "MRState":
        """
        從 MRInfo 建立 MRState
        
        Args:
            mr_info: MR 資訊物件
            
        Returns:
            MRState 物件
        """
        return cls(
            mr_id=mr_info.id,
            project_slug=mr_info.project_name,
            iid=mr_info.iid,
            state=mr_info.state,
            head_commit_sha="",  # 會在後續更新
        )
