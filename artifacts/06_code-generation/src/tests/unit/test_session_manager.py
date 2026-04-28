"""session_manager.py の単体テスト"""
import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pytest
from unittest.mock import patch, MagicMock

from session.session_manager import SessionManagerFactory


class TestSessionManagerFactory:
    def test_generate_session_id_パターン一致(self):
        sid = SessionManagerFactory.generate_session_id()
        assert re.match(r"^\d{14}_[a-f0-9]{8}$", sid), f"不正なsession_id: {sid}"

    def test_generate_session_id_一意性(self):
        ids = {SessionManagerFactory.generate_session_id() for _ in range(10)}
        assert len(ids) == 10

    def test_get_storage_dir_が正しい値を返す(self):
        assert SessionManagerFactory.get_storage_dir() == "data/sessions/"

    def test_create_session_manager_がFileSessionManagerを返す(self):
        from strands.session.file_session_manager import FileSessionManager
        sm = SessionManagerFactory.create_session_manager("test_session_id")
        assert isinstance(sm, FileSessionManager)

    def test_get_session_path_が正しいパスを返す(self):
        path = SessionManagerFactory.get_session_path("abc123")
        assert "abc123" in path
        assert path.startswith("data/sessions/")
