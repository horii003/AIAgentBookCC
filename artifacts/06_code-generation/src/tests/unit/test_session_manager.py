"""Unit tests for session/session_manager.py"""
import os
import re
import pytest
from unittest.mock import patch, MagicMock

from session.session_manager import SessionManagerFactory


class TestGenerateSessionId:
    def test_format_without_prefix(self):
        sid = SessionManagerFactory.generate_session_id()
        # Expected: YYYYMMDD_HHMMSS_uuid8
        assert re.match(r"^\d{8}_\d{6}_[0-9a-f]{8}$", sid), f"Unexpected format: {sid}"

    def test_format_with_prefix(self):
        sid = SessionManagerFactory.generate_session_id(prefix="test")
        assert sid.startswith("test_")
        assert re.match(r"^test_\d{8}_\d{6}_[0-9a-f]{8}$", sid), f"Unexpected format: {sid}"

    def test_uniqueness(self):
        ids = {SessionManagerFactory.generate_session_id() for _ in range(10)}
        assert len(ids) == 10


class TestGetStorageDir:
    def test_returns_string(self):
        SessionManagerFactory._storage_dir = None
        result = SessionManagerFactory.get_storage_dir()
        assert isinstance(result, str)

    def test_creates_directory(self, tmp_path):
        SessionManagerFactory._storage_dir = None
        with patch("session.session_manager._SESSION_STORAGE_DIR", str(tmp_path / "sessions")):
            result = SessionManagerFactory.get_storage_dir()
            assert os.path.isdir(result)
        SessionManagerFactory._storage_dir = None


class TestCreate:
    def test_returns_file_session_manager(self):
        from strands.session.file_session_manager import FileSessionManager
        with patch("session.session_manager.FileSessionManager") as MockFSM:
            mock_instance = MagicMock(spec=FileSessionManager)
            MockFSM.return_value = mock_instance
            with patch.object(SessionManagerFactory, "get_storage_dir", return_value="data/sessions"):
                result = SessionManagerFactory.create("test-session-001")
        assert result is mock_instance

    def test_passes_session_id_and_storage_dir(self):
        with patch("session.session_manager.FileSessionManager") as MockFSM:
            with patch.object(SessionManagerFactory, "get_storage_dir", return_value="data/sessions"):
                SessionManagerFactory.create("my-session")
        MockFSM.assert_called_once_with(session_id="my-session", storage_dir="data/sessions")


class TestGetSessionPath:
    def test_path_contains_session_id(self):
        with patch.object(SessionManagerFactory, "get_storage_dir", return_value="data/sessions"):
            path = SessionManagerFactory.get_session_path("abc123")
        assert "abc123" in path
        assert "data/sessions" in path or os.sep.join(["data", "sessions"]) in path
