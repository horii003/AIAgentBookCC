"""セッション管理機能

FileSessionManagerを使用してエージェントの会話履歴と状態を永続化する。
"""
import os
import uuid
from datetime import datetime

from strands.session.file_session_manager import FileSessionManager

_SESSION_STORAGE_DIR = "data/sessions"


class SessionManagerFactory:
    """セッションマネージャーのファクトリークラス"""

    _storage_dir: str | None = None

    @classmethod
    def generate_session_id(cls, prefix: str = "") -> str:
        """一意のセッションIDを生成する。

        形式:
            prefixなし: "YYYYMMDD_HHMMSS_uuid8"
            prefixあり: "prefix_YYYYMMDD_HHMMSS_uuid8"
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        short_uuid = uuid.uuid4().hex[:8]
        if prefix:
            return f"{prefix}_{timestamp}_{short_uuid}"
        return f"{timestamp}_{short_uuid}"

    @classmethod
    def get_storage_dir(cls) -> str:
        """セッションの保存先ディレクトリを取得し、存在しない場合は作成する"""
        if cls._storage_dir is None:
            cls._storage_dir = _SESSION_STORAGE_DIR
        os.makedirs(cls._storage_dir, exist_ok=True)
        return cls._storage_dir

    @classmethod
    def create(cls, session_id: str) -> FileSessionManager:
        """FileSessionManagerのインスタンスを作成して返す"""
        storage_dir = cls.get_storage_dir()
        return FileSessionManager(session_id=session_id, storage_dir=storage_dir)

    @classmethod
    def create_session_manager(cls, session_id: str) -> FileSessionManager:
        """create() の別名（後方互換用）"""
        return cls.create(session_id)

    @classmethod
    def get_session_path(cls, session_id: str) -> str:
        """指定されたセッションIDのセッションディレクトリパスを取得する"""
        storage_dir = cls.get_storage_dir()
        return os.path.join(storage_dir, session_id)
