"""SessionManagerFactoryの単体テスト"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import re
import pytest
from unittest.mock import patch, MagicMock
from session.session_manager import SessionManagerFactory


class TestSessionManagerFactory:
    def setup_method(self):
        # テスト間でのキャッシュリセット
        SessionManagerFactory._storage_dir = None

    def test_generate_session_idの書式確認(self):
        session_id = SessionManagerFactory.generate_session_id()
        pattern = r"^\d{8}_\d{6}_[0-9a-f]{8}$"
        assert re.match(pattern, session_id), f"形式不一致: {session_id}"

    def test_generate_session_idプレフィックスあり(self):
        session_id = SessionManagerFactory.generate_session_id("test")
        pattern = r"^test_\d{8}_\d{6}_[0-9a-f]{8}$"
        assert re.match(pattern, session_id), f"形式不一致: {session_id}"

    def test_generate_session_idの一意性(self):
        ids = {SessionManagerFactory.generate_session_id() for _ in range(10)}
        assert len(ids) == 10

    def test_get_storage_dirがディレクトリを作成する(self, tmp_path):
        with patch("session.session_manager.Path") as mock_path_cls:
            mock_root = MagicMock()
            mock_storage = MagicMock()
            mock_path_cls.return_value.parent.parent = mock_root
            mock_root.__truediv__ = lambda self, x: mock_storage
            mock_storage.__truediv__ = lambda self, x: mock_storage
            mock_storage.mkdir = MagicMock()
            mock_storage.__str__ = lambda self: str(tmp_path / "storage" / "sessions")
            SessionManagerFactory._storage_dir = None
            result = str(tmp_path / "storage" / "sessions")
            # 実際のパスで確認
        storage_dir = SessionManagerFactory.get_storage_dir()
        assert os.path.isdir(storage_dir)

    def test_get_storage_dirがキャッシュを使用する(self):
        first = SessionManagerFactory.get_storage_dir()
        second = SessionManagerFactory.get_storage_dir()
        assert first == second

    def test_create_session_managerがFileSessionManagerを返す(self):
        with patch("session.session_manager.FileSessionManager") as mock_fsm:
            mock_fsm.return_value = MagicMock()
            manager = SessionManagerFactory.create_session_manager("test_session")
            mock_fsm.assert_called_once()
            assert manager is not None

    def test_get_session_pathがパスを返す(self):
        path = SessionManagerFactory.get_session_path("my_session")
        assert "my_session" in path
