"""
MR 掃描器測試
"""

import pytest
from unittest.mock import Mock

from src.scanner.mr_scanner import MRScanner, ScanResult
from src.gitlab_.models import MRInfo


class TestMRScanner:
    """MR 掃描器的測試"""

    def test_scanner_init(self):
        """初始化掃描器"""
        mock_client = Mock()
        mock_state_manager = Mock()
        
        scanner = MRScanner(mock_client, mock_state_manager)
        
        assert scanner is not None
        assert scanner.client == mock_client

    def test_filter_mrs_exclude_wip(self):
        """篩選出 WIP MR"""
        mock_client = Mock()
        mock_state_manager = Mock()
        
        # 建立測試用 MR
        wip_mr = MRInfo(
            id=1, project_id=1, project_name="test/project", iid=1,
            title="WIP: Test MR", description="", state="opened",
            author="test", created_at="", updated_at="",
            source_branch="feature", target_branch="main",
            web_url="", draft=False, work_in_progress=True
        )
        normal_mr = MRInfo(
            id=2, project_id=1, project_name="test/project", iid=2,
            title="Test MR", description="", state="opened",
            author="test", created_at="", updated_at="",
            source_branch="feature", target_branch="main",
            web_url="", draft=False, work_in_progress=False
        )
        
        scanner = MRScanner(mock_client, mock_state_manager)
        filtered = scanner._filter_mrs([wip_mr, normal_mr], exclude_wip=True, exclude_draft=False)
        
        assert len(filtered) == 1
        assert filtered[0].iid == 2

    def test_filter_mrs_exclude_draft(self):
        """篩選出草稿 MR"""
        mock_client = Mock()
        mock_state_manager = Mock()
        
        draft_mr = MRInfo(
            id=1, project_id=1, project_name="test/project", iid=1,
            title="Draft MR", description="", state="opened",
            author="test", created_at="", updated_at="",
            source_branch="feature", target_branch="main",
            web_url="", draft=True, work_in_progress=False
        )
        normal_mr = MRInfo(
            id=2, project_id=1, project_name="test/project", iid=2,
            title="Test MR", description="", state="opened",
            author="test", created_at="", updated_at="",
            source_branch="feature", target_branch="main",
            web_url="", draft=False, work_in_progress=False
        )
        
        scanner = MRScanner(mock_client, mock_state_manager)
        filtered = scanner._filter_mrs([draft_mr, normal_mr], exclude_wip=False, exclude_draft=True)
        
        assert len(filtered) == 1
        assert filtered[0].iid == 2

    def test_filter_mrs_exclude_both(self):
        """同時篩選 WIP 和草稿 MR"""
        mock_client = Mock()
        mock_state_manager = Mock()
        
        wip_mr = MRInfo(
            id=1, project_id=1, project_name="test/project", iid=1,
            title="WIP: Test", description="", state="opened",
            author="test", created_at="", updated_at="",
            source_branch="feature", target_branch="main",
            web_url="", draft=False, work_in_progress=True
        )
        draft_mr = MRInfo(
            id=2, project_id=1, project_name="test/project", iid=2,
            title="Draft", description="", state="opened",
            author="test", created_at="", updated_at="",
            source_branch="feature", target_branch="main",
            web_url="", draft=True, work_in_progress=False
        )
        normal_mr = MRInfo(
            id=3, project_id=1, project_name="test/project", iid=3,
            title="Test MR", description="", state="opened",
            author="test", created_at="", updated_at="",
            source_branch="feature", target_branch="main",
            web_url="", draft=False, work_in_progress=False
        )
        
        scanner = MRScanner(mock_client, mock_state_manager)
        filtered = scanner._filter_mrs([wip_mr, draft_mr, normal_mr], exclude_wip=True, exclude_draft=True)
        
        assert len(filtered) == 1
        assert filtered[0].iid == 3

    def test_filter_mrs_include_all(self):
        """不篩選任何 MR"""
        mock_client = Mock()
        mock_state_manager = Mock()
        
        mrs = [
            MRInfo(
                id=i, project_id=1, project_name="test/project", iid=i,
                title=f"MR {i}", description="", state="opened",
                author="test", created_at="", updated_at="",
                source_branch="feature", target_branch="main",
                web_url="", draft=i==2, work_in_progress=i==1
            ) for i in range(1, 4)
        ]
        
        scanner = MRScanner(mock_client, mock_state_manager)
        filtered = scanner._filter_mrs(mrs, exclude_wip=False, exclude_draft=False)
        
        assert len(filtered) == 3

    def test_scan_result_creation(self):
        """建立掃描結果"""
        mr = MRInfo(
            id=1, project_id=1, project_name="test/project", iid=1,
            title="Test MR", description="", state="opened",
            author="test", created_at="", updated_at="",
            source_branch="feature", target_branch="main",
            web_url="", draft=False, work_in_progress=False
        )
        
        result = ScanResult(
            project="test/project",
            merge_requests=[mr],
            error=None
        )
        
        assert result.project == "test/project"
        assert len(result.merge_requests) == 1
        assert result.error is None

    def test_scan_result_with_error(self):
        """建立帶有錯誤的掃描結果"""
        result = ScanResult(
            project="test/project",
            merge_requests=[],
            error="掃描失敗: 連接錯誤"
        )
        
        assert result.project == "test/project"
        assert len(result.merge_requests) == 0
        assert result.error is not None


    def test_scan_handles_client_exception(self):
        """當 client 發生例外時，scan 應回傳帶有 error 的 ScanResult"""
        mock_client = Mock()
        mock_state_manager = Mock()

        # 設定 client 在取得 MR 時拋出例外
        mock_client.get_merge_requests.side_effect = Exception("API error")

        scanner = MRScanner(mock_client, mock_state_manager)
        results = scanner.scan(["group/project"], exclude_wip=True, exclude_draft=True)

        assert len(results) == 1
        assert results[0].error is not None
        assert "API error" in results[0].error


def test_scan_success_calls_filter_and_returns_results():
    from src.scanner.mr_scanner import MRScanner
    from src.gitlab_.models import MRInfo

    mock_client = Mock()
    mock_state_manager = Mock()

    mr = MRInfo(
        id=1, project_id=1, project_name="test/project", iid=1,
        title="Test MR", description="", state="opened",
        author="test", created_at="", updated_at="",
        source_branch="feature", target_branch="main",
        web_url="", draft=False, work_in_progress=False
    )

    mock_client.get_merge_requests.return_value = [mr]

    scanner = MRScanner(mock_client, mock_state_manager)
    results = scanner.scan(["group/project"], exclude_wip=True, exclude_draft=True)

    assert len(results) == 1
    assert results[0].project == "group/project"
    assert len(results[0].merge_requests) == 1
