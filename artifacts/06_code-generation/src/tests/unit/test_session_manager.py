"""session_manager.py の単体テスト"""
import pytest
from unittest.mock import patch, MagicMock

from session.session_manager import SessionManagerFactory


class TestSessionManagerFactory:
    def test_create_returns_file_session_manager(self):
        """create() が FileSessionManager インスタンスを返すこと"""
        with patch("session.session_manager.FileSessionManager") as mock_fsm:
            mock_instance = MagicMock()
            mock_fsm.return_value = mock_instance
            result = SessionManagerFactory.create("test-session-id")
            assert result is mock_instance
            mock_fsm.assert_called_once_with(
                session_id="test-session-id",
                storage_dir="storage/sessions/",
            )

    def test_create_with_custom_storage_path(self):
        """storage_path が正しく設定されること"""
        with patch("session.session_manager.FileSessionManager") as mock_fsm:
            mock_fsm.return_value = MagicMock()
            SessionManagerFactory.create("sess-001", storage_path="custom/sessions/")
            mock_fsm.assert_called_once_with(
                session_id="sess-001",
                storage_dir="custom/sessions/",
            )
