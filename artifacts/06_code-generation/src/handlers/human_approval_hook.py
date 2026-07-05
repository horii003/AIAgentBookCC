"""Human-in-the-Loop承認フック

申請書生成ツールの実行直前に社員確認を行うフック。

【2層承認構造】
  1. プロンプト層: LLMが申請内容の下書きをユーザーに見せ、対話で確認する。
  2. フック層（このクラス）: BeforeToolCallEvent でツール実行直前に割り込み、
     コード側で必ず人間が確認することを保証する安全装置。

【責務の分離】
  このクラスは承認が必要なタイミングを検知する制御点のみ担当。
  UI入力は approval_callback に委譲する。
"""
import logging
from typing import Any, Callable, Optional

from strands.hooks import BeforeToolCallEvent, HookProvider, HookRegistry

_logger = logging.getLogger(__name__)


class HumanApprovalHook(HookProvider):
    """指定ツール実行前に人間の承認を求めるフック"""

    APPROVAL_REQUIRED_TOOLS: frozenset = frozenset({
        "generate_transport_expense_form",
        "generate_general_expense_form",
    })

    def __init__(
        self,
        approval_callback: Callable[[str, dict], tuple],
        approval_required_tools: Optional[list] = None,
    ):
        """
        Args:
            approval_callback: 承認を求めるコールバック関数。
                               戻り値: (approved: bool, feedback: str)
                                 (True,  "")         : 承認
                                 (False, "CANCEL")   : キャンセル
                                 (False, "修正内容") : 修正要望
            approval_required_tools: 承認対象ツール名のリスト（Noneでデフォルト使用）
        """
        self.approval_callback = approval_callback
        self.approval_required_tools: frozenset = (
            frozenset(approval_required_tools)
            if approval_required_tools is not None
            else self.APPROVAL_REQUIRED_TOOLS
        )

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        registry.add_callback(BeforeToolCallEvent, self._on_before_tool_call)

    def _on_before_tool_call(self, event: BeforeToolCallEvent) -> None:
        tool_name = event.tool_use.get("name", "") if event.tool_use else ""
        tool_params = event.tool_use.get("input", {}) if event.tool_use else {}

        if tool_name not in self.approval_required_tools:
            return

        _logger.info("HumanApprovalHook: 承認確認開始 tool_name=%s", tool_name)

        approved, feedback = self.approval_callback(tool_name, tool_params)

        if approved:
            _logger.info("HumanApprovalHook: 承認OK tool_name=%s", tool_name)
            return

        cancel_message = self._build_cancel_message(tool_name, feedback)
        _logger.info(
            "HumanApprovalHook: ツールキャンセル tool_name=%s feedback=%s",
            tool_name,
            feedback,
        )
        event.cancel_tool = cancel_message

    def _build_cancel_message(self, tool_name: str, feedback: str) -> str:
        """キャンセルメッセージを生成する。

        event.cancel_tool に設定した文字列はツール結果としてLLMに返却される。
        """
        if not feedback or feedback == "CANCEL":
            return "申請者がキャンセルを選択しました。申請処理を中止してください。"
        return (
            f"申請者から修正要望があります。内容を修正して再度確認を求めてください。\n"
            f"修正内容: {feedback}"
        )
