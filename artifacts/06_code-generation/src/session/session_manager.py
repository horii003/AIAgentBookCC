"""セッション管理機能

FileSessionManager を使用してエージェントの会話履歴と状態を永続化する。
"""
import uuid
from datetime import datetime

from strands.session.file_session_manager import FileSessionManager


class SessionManagerFactory:
    """セッションマネージャーのファクトリークラス"""

    @classmethod
    def generate_session_id(cls) -> str:
        """一意のセッションIDを生成する。

        形式: "{タイムスタンプ（秒単位）}_{UUID（8文字）}"
        例: "20260323153045_a1b2c3d4"
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        uid = uuid.uuid4().hex[:8]
        return f"{timestamp}_{uid}"

    @classmethod
    def get_storage_dir(cls) -> str:
        """セッションの保存先ディレクトリを返す。"""
        return "data/sessions/"

    @classmethod
    def create_session_manager(cls, session_id: str) -> FileSessionManager:
        """FileSessionManager のインスタンスを生成して返す。

        Args:
            session_id: セッションID
        """
        return FileSessionManager(
            session_id=session_id,
            storage_path=cls.get_storage_dir(),
        )

    @classmethod
    def get_session_path(cls, session_id: str) -> str:
        """指定セッションIDのセッションファイルパスを返す。"""
        return f"{cls.get_storage_dir()}{session_id}.json"
