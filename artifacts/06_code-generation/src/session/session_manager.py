"""セッション管理機能

FileSessionManagerを使用してエージェントの会話履歴と状態を永続化します。
"""
from strands.session.file_session_manager import FileSessionManager


class SessionManagerFactory:
    """セッションマネージャーのファクトリークラス"""

    @classmethod
    def create(
        cls,
        session_id: str,
        storage_path: str = "storage/sessions/",
    ) -> FileSessionManager:
        """FileSessionManager のインスタンスを作成する。

        Args:
            session_id: セッションID
            storage_path: セッションファイルの保存先ディレクトリ

        Returns:
            FileSessionManager: 設定済みのセッションマネージャーインスタンス
        """
        return FileSessionManager(
            session_id=session_id,
            storage_dir=storage_path,
        )
