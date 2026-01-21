"""
測試 Config._load_projects_from_file 在 open/IOError 時的處理
"""

import builtins
from unittest.mock import mock_open, patch
import pytest

from src.config import Config
from src.utils.exceptions import ConfigError


def test_load_projects_from_file_ioerror(tmp_path):
    p = tmp_path / "proj.txt"
    p.write_text("group/proj\n")

    # 模擬 open 拋出 IOError
    with patch('builtins.open', mock_open()) as m:
        m.side_effect = IOError('disk error')
        with pytest.raises(ConfigError):
            Config._load_projects_from_file(str(p))
