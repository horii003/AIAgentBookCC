"""HumanApprovalHookの実装

TOOL-002（申請書生成ツール）呼び出し前に利用者のOK/修正/キャンセルを取得する承認ゲート。
AG-002（交通費精算）とAG-003（経費精算）に登録する。
"""
import json
import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Callable, List, Optional, Tuple

from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import BeforeToolCallEvent

__all__ = ["HumanApprovalHook"]

_APPROVAL_LOG_PATH = "logs/approval.log"
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
_BACKUP_COUNT = 5

_INPUT_NORMALIZE_MAP = {
    "ok": "OK", "O": "OK", "o": "OK", "はい": "OK", "1": "OK",
    "修正": "修正", "修正する": "修正", "2": "修正",
    "キャンセル": "キャンセル", "cancel": "キャンセル", "Cancel": "キャンセル", "3": "キャンセル",
}
_MAX_INVALID_ATTEMPTS = 5


def _normalize_input(raw: str) -> Optional[str]:
    """ユーザー入力を正規化して OK / 修正 / キャンセル を返す。無効な場合は None。"""
    stripped = raw.strip()
    if stripped.upper() == "OK":
        return "OK"
    return _INPUT_NORMALIZE_MAP.get(stripped)


class HumanApprovalHook(HookProvider):
    """TOOL-002呼び出し前の利用者承認ゲート"""

    def __init__(
        self,
        tool_names: List[str],
        approval_callback: Optional[Callable[[str, dict], Tuple[bool, str]]] = None,
    ) -> None:
        self._tool_names = tool_names
        self._approval_callback = approval_callback
        self._logger = logging.getLogger(__name__)
        self._setup_approval_logger()

    def _setup_approval_logger(self) -> None:
        """logs/approval.log へのRotatingFileHandlerを設定する"""
        self._approval_logger = logging.getLogger("approval_log")
        if self._approval_logger.handlers:
            return
        try:
            os.makedirs("logs", exist_ok=True)
            handler = RotatingFileHandler(
                _APPROVAL_LOG_PATH,
                maxBytes=_MAX_BYTES,
                backupCount=_BACKUP_COUNT,
                encoding="utf-8",
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._approval_logger.addHandler(handler)
            self._approval_logger.setLevel(logging.INFO)
            self._approval_logger.propagate = False
        except Exception as exc:
            print(f"[HumanApprovalHook] 承認ログハンドラー設定失敗: {exc}", file=sys.stderr)

    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        registry.add_callback(BeforeToolCallEvent, self._on_before_tool_call)

    def _on_before_tool_call(self, event: BeforeToolCallEvent) -> None:
        tool_use = event.tool_use if event.tool_use else {}
        tool_name = tool_use.get("name", "") if isinstance(tool_use, dict) else getattr(tool_use, "get", lambda k, d: d)("name", "")
        # Handle both dict and object tool_use
        if hasattr(tool_use, "__getitem__"):
            try:
                tool_name = tool_use.get("name", "")
            except Exception:
                tool_name = ""
        else:
            tool_name = getattr(tool_use, "name", "")

        if tool_name not in self._tool_names:
            self._logger.info(
                "[HumanApprovalHook] ツール名スルー: tool_name=%s （フィルタ対象外）", tool_name
            )
            return

        # Get tool params
        if hasattr(tool_use, "__getitem__"):
            try:
                tool_params = tool_use.get("input", {}) or {}
            except Exception:
                tool_params = {}
        else:
            tool_params = getattr(tool_use, "input", {}) or {}

        if self._approval_callback is not None:
            self._logger.info(
                "[HumanApprovalHook] 承認コールバック呼び出し: tool_name=%s", tool_name
            )
            try:
                approved, message = self._approval_callback(tool_name, tool_params)
            except Exception as exc:
                self._logger.warning(
                    "[HumanApprovalHook] コールバック例外: tool_name=%s, error=%s", tool_name, exc
                )
                event.cancel_tool = f"承認処理中にエラーが発生しました: {exc}"
                return

            if approved:
                self._log_approval(tool_name, "OK")
                self._logger.info("[HumanApprovalHook] 承認OK: tool_name=%s", tool_name)
                return
            elif message == "CANCEL":
                self._log_approval(tool_name, "キャンセル")
                self._logger.info("[HumanApprovalHook] キャンセル選択: tool_name=%s", tool_name)
                event.cancel_tool = "申請をキャンセルしました。"
            else:
                self._log_approval(tool_name, "修正")
                self._logger.info("[HumanApprovalHook] 修正選択: tool_name=%s", tool_name)
                event.cancel_tool = f"修正要望: {message}"
        else:
            self._default_approval(event, tool_name)

    def _default_approval(self, event: BeforeToolCallEvent, tool_name: str) -> None:
        """標準入力によるデフォルト承認処理（approval_callback 未設定時）"""
        self._logger.info(
            "[HumanApprovalHook] 承認プロンプト提示: tool_name=%s", tool_name
        )
        invalid_count = 0
        while True:
            print(
                "\n【申請書生成の確認】申請書の生成を実行します。"
                "「OK」「修正」「キャンセル」のいずれかを入力してください：",
                end=" ",
                flush=True,
            )
            try:
                raw = input()
            except EOFError:
                raw = "キャンセル"

            choice = _normalize_input(raw)
            if choice == "OK":
                self._log_approval(tool_name, "OK")
                self._logger.info("[HumanApprovalHook] 承認OK: tool_name=%s", tool_name)
                return
            elif choice == "修正":
                self._log_approval(tool_name, "修正")
                self._logger.info("[HumanApprovalHook] 修正選択: tool_name=%s", tool_name)
                event.cancel_tool = "修正を選択しました。収集情報を最初からやり直してください。"
                return
            elif choice == "キャンセル":
                self._log_approval(tool_name, "キャンセル")
                self._logger.info("[HumanApprovalHook] キャンセル選択: tool_name=%s", tool_name)
                event.cancel_tool = "申請をキャンセルしました。"
                return
            else:
                invalid_count += 1
                print("「OK」「修正」「キャンセル」のいずれかを入力してください。")
                if invalid_count >= _MAX_INVALID_ATTEMPTS:
                    self._log_approval(tool_name, "キャンセル")
                    event.cancel_tool = "申請をキャンセルしました。"
                    return

    def _log_approval(self, tool_name: str, choice: str) -> None:
        """承認操作をlogs/approval.logにJSON Lines形式で記録する"""
        record = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "tool_name": tool_name,
            "choice": choice,
        }
        try:
            self._approval_logger.info(json.dumps(record, ensure_ascii=False))
        except Exception as exc:
            print(
                f"[HumanApprovalHook] 承認ログ書き込み失敗: {exc}",
                file=sys.stderr,
            )
