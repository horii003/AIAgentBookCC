from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional


class SessionState(str, Enum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    WAITING = "WAITING"
    CLOSED = "CLOSED"
    TERMINATED = "TERMINATED"


class SessionData:
    def __init__(
        self,
        session_id: str,
        status: SessionState,
        applicant_name: str,
        application_date: str,
        created_at: str,
        updated_at: str,
    ) -> None:
        self.session_id = session_id
        self.status = status
        self.applicant_name = applicant_name
        self.application_date = application_date
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "status": self.status.value,
            "applicant_name": self.applicant_name,
            "application_date": self.application_date,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> SessionData:
        return cls(
            session_id=data["session_id"],
            status=SessionState(data["status"]),
            applicant_name=data.get("applicant_name", ""),
            application_date=data.get("application_date", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


class FileBasedSessionManager:
    def __init__(self, storage_path: str = "data/sessions") -> None:
        self._storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)

    def _session_file(self, session_id: str) -> str:
        return os.path.join(self._storage_path, f"{session_id}.json")

    def create_session(self, applicant_name: str, application_date: str) -> str:
        now = datetime.now()
        date_part = now.strftime("%Y%m%d")
        time_part = now.strftime("%H%M%S")
        uid = uuid.uuid4().hex[:8]
        session_id = f"{date_part}_{time_part}_{uid}"

        data = SessionData(
            session_id=session_id,
            status=SessionState.CREATED,
            applicant_name=applicant_name,
            application_date=application_date,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
        )
        with open(self._session_file(session_id), "w", encoding="utf-8") as f:
            json.dump(data.to_dict(), f, ensure_ascii=False, indent=2)
        return session_id

    def get_session(self, session_id: str) -> Optional[SessionData]:
        path = self._session_file(session_id)
        if not os.path.exists(path):
            return None
        with open(path, encoding="utf-8") as f:
            return SessionData.from_dict(json.load(f))

    def update_status(self, session_id: str, status: SessionState) -> None:
        data = self.get_session(session_id)
        if data is None:
            return
        data.status = status
        data.updated_at = datetime.now().isoformat()
        with open(self._session_file(session_id), "w", encoding="utf-8") as f:
            json.dump(data.to_dict(), f, ensure_ascii=False, indent=2)


class SessionManagerFactory:
    @staticmethod
    def create(storage_path: str = "data/sessions") -> FileBasedSessionManager:
        return FileBasedSessionManager(storage_path=storage_path)
