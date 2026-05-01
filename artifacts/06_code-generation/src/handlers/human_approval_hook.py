"""Human-in-the-Loop承認フック

申請書生成ツール呼び出し前に APR-001 承認ダイアログを提示するフック。
"""
import json
import logging
from datetime import datetime
from typing import Any, Callable

from strands.hooks import (
    HookProvider,
    HookRegistry,
    BeforeToolCallEvent,
)

logger = logging.getLogger("handlers.human_approval_hook")

APPROVAL_TOOL_NAMES = {
    "generate_transport_application",
    "generate_expense_application",
}
APPROVAL_INVALID_MAX = 3
AUDIT_LOG_HI_PATH = "logs/audit_log_hi.jsonl"


class HumanApprovalHook(HookProvider):
    """申請書生成ツール呼び出し前に APR-001 承認ダイアログを提示するフック。"""

    def __init__(self, approval_callback: Callable[[str, dict], tuple]) -> None:
        self.approval_callback = approval_callback
        self._invalid_input_count: int = 0

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        """フックの登録"""
        registry.add_callback(BeforeToolCallEvent, self._before_tool_call_handler)

    def _before_tool_call_handler(self, event: BeforeToolCallEvent) -> None:
        """BeforeToolCallEvent ハンドラー: 申請書生成ツール呼び出し前に APR-001 を実施する。"""
        tool_name = getattr(event, "tool_name", None)
        if tool_name not in APPROVAL_TOOL_NAMES:
            return

        self._invalid_input_count = 0
        tool_use = getattr(event, "tool_use", {}) or {}
        tool_params = tool_use.get("input", {}) if isinstance(tool_use, dict) else {}

        while True:
            result = self.approval_callback(tool_name, tool_params)

            if not isinstance(result, tuple) or len(result) != 2:
                self._invalid_input_count += 1
                if self._invalid_input_count >= APPROVAL_INVALID_MAX:
                    logger.warning(
                        f"APR-001: 不正入力が{APPROVAL_INVALID_MAX}回に達したためキャンセル処理: "
                        f"tool_name={tool_name}"
                    )
                    self._handle_cancelled(event, tool_name)
                    return
                continue

            approved, detail = result

            if approved:
                self._handle_approved(event, tool_name)
                return
            elif detail == "CANCEL":
                self._handle_cancelled(event, tool_name)
                return
            elif detail:
                self._handle_modify(event, tool_name, detail)
                return
            else:
                self._invalid_input_count += 1
                if self._invalid_input_count >= APPROVAL_INVALID_MAX:
                    logger.warning(
                        f"APR-001: 不正入力が{APPROVAL_INVALID_MAX}回に達したためキャンセル処理: "
                        f"tool_name={tool_name}"
                    )
                    self._handle_cancelled(event, tool_name)
                    return

    def _handle_approved(self, event: BeforeToolCallEvent, tool_name: str) -> None:
        """承認（OK）時の処理: ログを記録してツール実行を続行する。"""
        logger.info(f"APR-001 承認: tool_name={tool_name}")
        self._write_audit_log("APR-001_approved", tool_name)

    def _handle_modify(self, event: BeforeToolCallEvent, tool_name: str, modify_detail: str) -> None:
        """修正時の処理: ツール実行をキャンセルして修正フローへ戻す。"""
        logger.info(f"APR-001 修正要求: tool_name={tool_name}, detail={modify_detail}")
        event.cancel_tool = f"修正要求: {modify_detail}"

    def _handle_cancelled(self, event: BeforeToolCallEvent, tool_name: str) -> None:
        """キャンセル時の処理: ツール実行をキャンセルする。"""
        logger.warning(f"APR-001 キャンセル: tool_name={tool_name}")
        self._write_audit_log("APR-001_cancelled", tool_name)
        event.cancel_tool = "キャンセル"

    def _write_audit_log(self, event_name: str, tool_name: str) -> None:
        """強化監査ログ（audit_log_hi.jsonl）に承認情報を記録する。"""
        try:
            entry = {
                "event": event_name,
                "tool_name": tool_name,
                "timestamp": datetime.now().isoformat(),
            }
            with open(AUDIT_LOG_HI_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"監査ログ書き込み失敗: {str(e)}", exc_info=True)
