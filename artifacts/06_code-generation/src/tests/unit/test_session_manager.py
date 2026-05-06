# 参照: BD-05 セッション管理基本設計書
"""session/session_manager.py の単体テスト"""
import sys
import os
import json
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from session.session_manager import SessionManager


class TestSessionManager:
    """SessionManager のテスト"""

    def test_create_session_creates_file(self, tmp_path):
        """create_session()でJSONファイルが作成されること。"""
        sm = SessionManager(session_id="test_session_001", storage_path=str(tmp_path))
        sm.create_session()
        session_file = tmp_path / "test_session_001.json"
        assert session_file.exists()

    def test_create_session_initial_status(self, tmp_path):
        """create_session()でsession_statusがCREATEDであること。"""
        sm = SessionManager(session_id="test_session_002", storage_path=str(tmp_path))
        sm.create_session()
        data = sm.load_session()
        assert data is not None
        assert data["session_status"] == "CREATED"
        assert data["session_id"] == "test_session_002"

    def test_save_and_load_session(self, tmp_path):
        """save_session()後にload_session()で同一データが取得できること。"""
        sm = SessionManager(session_id="test_session_003", storage_path=str(tmp_path))
        test_data = {
            "session_id": "test_session_003",
            "session_status": "ACTIVE",
            "applicant_name": "山田太郎",
        }
        sm.save_session(test_data)
        loaded = sm.load_session()
        assert loaded is not None
        assert loaded["session_status"] == "ACTIVE"
        assert loaded["applicant_name"] == "山田太郎"

    def test_load_session_returns_none_for_missing(self, tmp_path):
        """存在しないセッションIDでload_session()がNoneを返すこと（例外を発生させないこと）。"""
        sm = SessionManager(session_id="nonexistent_session", storage_path=str(tmp_path))
        result = sm.load_session()
        assert result is None

    def test_update_status(self, tmp_path):
        """update_status()でセッションステータスが更新されること。"""
        sm = SessionManager(session_id="test_session_004", storage_path=str(tmp_path))
        sm.create_session()
        sm.update_status("ACTIVE")
        data = sm.load_session()
        assert data["session_status"] == "ACTIVE"

    def test_delete_session(self, tmp_path):
        """delete_session()でファイルが削除されること。"""
        sm = SessionManager(session_id="test_session_005", storage_path=str(tmp_path))
        sm.create_session()
        session_file = tmp_path / "test_session_005.json"
        assert session_file.exists()
        sm.delete_session()
        assert not session_file.exists()

    def test_delete_nonexistent_session_no_error(self, tmp_path):
        """存在しないセッションのdelete_session()がエラーなく完了すること。"""
        sm = SessionManager(session_id="nonexistent", storage_path=str(tmp_path))
        sm.delete_session()  # 例外が発生しないこと

    def test_generate_session_id_format(self):
        """generate_session_id()が正しい形式のIDを返すこと。"""
        session_id = SessionManager.generate_session_id()
        assert isinstance(session_id, str)
        parts = session_id.split("_")
        assert len(parts) == 2
        # タイムスタンプ部分（14文字: YYYYMMDDHHMMSS）
        assert len(parts[0]) == 14
        assert parts[0].isdigit()
        # UUID部分（8文字の16進数）
        assert len(parts[1]) == 8
        assert all(c in "0123456789abcdef" for c in parts[1])

    def test_storage_directory_auto_created(self, tmp_path):
        """SessionManager初期化時にストレージディレクトリが自動作成されること。"""
        new_dir = tmp_path / "sessions" / "sub"
        sm = SessionManager(session_id="test_auto", storage_path=str(new_dir))
        assert new_dir.exists()
