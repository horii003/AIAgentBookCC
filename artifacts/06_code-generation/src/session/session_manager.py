# 参照: BD-05 セッション管理基本設計書, SD-03 セッション管理方針
"""セッション管理機能

申請フローの進捗状態（業務コンテキスト・フロー進捗・成果物参照）をセッション単位で
JSONファイルに永続化する。Strands AgentsのFileSessionManagerをラップして利用する。
セッション再開（resume）時にセッション状態ファイルから進捗を復元し、申請フローを継続できる。
"""
import os
import uuid
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from strands.session.file_session_manager import FileSessionManager
    _STRANDS_AVAILABLE = True
except ImportError:
    _STRANDS_AVAILABLE = False
    # strands未インストール環境向けスタブ
    class FileSessionManager:
        def __init__(self, session_id: str, storage_path: str):
            self.session_id = session_id
            self.storage_path = storage_path


class SessionManager:
    """セッション状態ファイル（data/sessions/{session_id}.json）の読み書き・生成・削除を担うクラス。

    責務: 全エージェント（AG-001〜AG-003）が共通して使用するセッション管理機能を提供する。
    制約:
      - セッション状態の保存はファイルベース（JSON）のみ
      - CLOSED/TERMINATED時にセッション状態ファイルを削除する（機微情報保護）
      - session_idはLLMのプロンプトに含めない。invocation_state経由のみで受け渡す
    """

    # R10: セッション保存先（プロジェクトルートからの相対パス）
    DEFAULT_STORAGE_PATH = "data/sessions/"

    def __init__(self, session_id: str, storage_path: str = DEFAULT_STORAGE_PATH):
        """
        Args:
            session_id: セッション識別子
            storage_path: セッション状態ファイルの保存先ディレクトリ
        """
        self.session_id = session_id
        self.storage_path = storage_path
        # ストレージディレクトリを自動作成する
        Path(storage_path).mkdir(parents=True, exist_ok=True)
        self._session_file_path = os.path.join(storage_path, f"{session_id}.json")

        # Strands AgentsのFileSessionManagerインスタンス（Agentに渡す用）
        if _STRANDS_AVAILABLE:
            self._file_session_manager = FileSessionManager(
                session_id=session_id,
                storage_path=storage_path,
            )
        else:
            self._file_session_manager = None

        logger.debug(
            "SessionManager initialized: session_id=%s, storage_path=%s",
            session_id,
            storage_path,
        )

    @property
    def file_session_manager(self):
        """Strands AgentsのFileSessionManagerインスタンスを返す（Agentのsession_managerパラメータに渡す用）。"""
        return self._file_session_manager

    def create_session(self) -> None:
        """初期状態でセッション状態ファイルを作成する。

        session_statusをCREATEDで初期化してJSONファイルを作成する。
        """
        initial_state = {
            "session_id": self.session_id,
            "session_status": "CREATED",
            "created_at": datetime.now().isoformat(),
        }
        self.save_session(initial_state)
        logger.info("Session created: session_id=%s", self.session_id)

    def load_session(self) -> dict | None:
        """セッション状態ファイルを読み込みdict返却する。

        Returns:
            セッション状態辞書（dict）またはNone（ファイル不存在時）
            例外を発生させない設計とする（BDサ:4.2参照）。
        """
        if not os.path.exists(self._session_file_path):
            return None
        try:
            with open(self._session_file_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to load session: session_id=%s, error=%s", self.session_id, e)
            return None

    def save_session(self, session_data: dict) -> None:
        """更新後のセッション状態辞書をJSONファイルに上書き保存する。

        Args:
            session_data: 保存するセッション状態辞書
        """
        try:
            with open(self._session_file_path, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            logger.debug("Session saved: session_id=%s", self.session_id)
        except Exception as e:
            logger.error("Failed to save session: session_id=%s, error=%s", self.session_id, e, exc_info=True)

    def update_status(self, new_status: str) -> None:
        """セッションステータスを更新する。

        Args:
            new_status: 新しいステータス（CREATED/ACTIVE/WAITING/CLOSED/TERMINATEDのいずれか）
        """
        session_data = self.load_session() or {"session_id": self.session_id}
        session_data["session_status"] = new_status
        session_data["updated_at"] = datetime.now().isoformat()
        self.save_session(session_data)
        logger.info("Session status updated: session_id=%s, status=%s", self.session_id, new_status)

    def delete_session(self) -> None:
        """セッション終了時（CLOSED/TERMINATED）にセッション状態ファイルを削除する（機微情報保護）。"""
        if os.path.exists(self._session_file_path):
            try:
                os.remove(self._session_file_path)
                logger.info("Session deleted: session_id=%s", self.session_id)
            except Exception as e:
                logger.error("Failed to delete session file: session_id=%s, error=%s", self.session_id, e)

    @staticmethod
    def generate_session_id() -> str:
        """一意のセッションIDを生成する。

        Returns:
            str: `{タイムスタンプ（秒単位）}_{UUID（8文字）}` 形式のセッションID
            例: 20260323153045_a1b2c3d4
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_part = uuid.uuid4().hex[:8]
        return f"{timestamp}_{random_part}"
