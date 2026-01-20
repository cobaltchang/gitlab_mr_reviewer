"""
測試 MRScanner 在 MR 物件缺少 draft 屬性時的行為
"""

from src.scanner.mr_scanner import MRScanner
from unittest.mock import Mock
from src.gitlab_.models import MRInfo


def test_filter_mrs_with_none_attrs():
    mock_client = Mock()
    mock_state_manager = Mock()

    # 建立 MRInfo，其中 draft 設為 None、work_in_progress 設為 True
    mr = MRInfo(
        id=1, project_id=1, project_name="g/p", iid=1,
        title="t", description="", state="opened",
        author="a", created_at="", updated_at="",
        source_branch="f", target_branch="m", web_url="",
        draft=None, work_in_progress=True
    )

    scanner = MRScanner(mock_client, mock_state_manager)
    filtered = scanner._filter_mrs([mr], exclude_wip=True, exclude_draft=True)

    # 因為 work_in_progress=True，應被排除
    assert filtered == []
