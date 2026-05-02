import sys
import os
import re
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from session.session_manager import FileBasedSessionManager, SessionManagerFactory, SessionState


SESSION_ID_PATTERN = re.compile(r"^\d{8}_\d{6}_[0-9a-f]{8}$")


class TestFileBasedSessionManager:
    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        self.mgr = FileBasedSessionManager(storage_path=self._tmpdir)

    def test_create_session_returns_valid_id(self):
        sid = self.mgr.create_session("田中太郎", "2026-05-02")
        assert SESSION_ID_PATTERN.match(sid), f"ID形式が不正: {sid}"

    def test_get_session_after_create(self):
        sid = self.mgr.create_session("田中太郎", "2026-05-02")
        data = self.mgr.get_session(sid)
        assert data is not None
        assert data.session_id == sid
        assert data.applicant_name == "田中太郎"
        assert data.status == SessionState.CREATED

    def test_get_session_not_found_returns_none(self):
        result = self.mgr.get_session("nonexistent_session_id")
        assert result is None

    def test_update_status(self):
        sid = self.mgr.create_session("田中太郎", "2026-05-02")
        self.mgr.update_status(sid, SessionState.ACTIVE)
        data = self.mgr.get_session(sid)
        assert data.status == SessionState.ACTIVE

    def test_update_status_nonexistent_does_not_raise(self):
        self.mgr.update_status("nonexistent", SessionState.CLOSED)


class TestSessionManagerFactory:
    def test_create_returns_manager(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = SessionManagerFactory.create(storage_path=tmpdir)
            assert isinstance(mgr, FileBasedSessionManager)
