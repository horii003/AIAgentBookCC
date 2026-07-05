"""セッション管理機能

FileSessionManagerを使用してエージェントの会話履歴と状態を永続化する。
"""
import os
import uuid
from datetime import datetime
from pathlib import Path

from strands.session.file_session_manager import FileSessionManager


class SessionManagerFactory:
    """セッションマネージャーのファクトリークラス"""

    _storage_dir: str = None

    @classmethod
    def generate_session_id(cls, prefix: str = "") -> str:
        """一意のセッションIDを生成する。

        Returns:
            str: "YYYYMMDD_HHMMSS_uuid8" または "prefix_YYYYMMDD_HHMMSS_uuid8"
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_part = uuid.uuid4().hex[:8]
        if prefix:
            return f"{prefix}_{timestamp}_{unique_part}"
        return f"{timestamp}_{unique_part}"

    @classmethod
    def get_storage_dir(cls) -> str:
        """セッションの保存先ディレクトリを取得する。ディレクトリが存在しない場合は自動作成する。"""
        if cls._storage_dir is not None:
            return cls._storage_dir

        project_root = Path(__file__).parent.parent
        storage_path = project_root / "storage" / "sessions"
        storage_path.mkdir(parents=True, exist_ok=True)
        cls._storage_dir = str(storage_path)
        return cls._storage_dir

    @classmethod
    def create_session_manager(cls, session_id: str) -> FileSessionManager:
        """FileSessionManagerのインスタンスを作成する。

        Args:
            session_id: セッションID

        Returns:
            FileSessionManager: セッションマネージャーのインスタンス
        """
        storage_dir = cls.get_storage_dir()
        return FileSessionManager(session_id=session_id, storage_dir=storage_dir)

    @classmethod
    def get_session_path(cls, session_id: str) -> str:
        """指定されたセッションIDのセッションディレクトリパスを取得する。"""
        storage_dir = cls.get_storage_dir()
        return os.path.join(storage_dir, session_id)
