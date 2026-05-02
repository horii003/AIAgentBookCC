from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

_APPROVAL_TOOLS = frozenset({
    "generate_transport_expense_form",
    "generate_expense_reimbursement_form",
})

# Module-level approval callback — replaced by patch_human_approval_hook() in tests/evals
approval_callback: Callable[[str, dict], tuple[bool, str]] = lambda tool_name, params: (True, "OK")


def _default_cli_approval_callback(tool_name: str, params: dict) -> tuple[bool, str]:
    confirmation_message = params.get("confirmation_message", "")
    print(confirmation_message)
    max_retries = 3
    for _ in range(max_retries):
        choice = input("選択してください (1/2/3): ").strip()
        if choice == "1":
            return True, "OK"
        elif choice == "2":
            return False, "修正"
        elif choice == "3":
            print("申請をキャンセルしました。またいつでもご相談ください。")
            return False, "キャンセル"
        else:
            print("1、2、3 のいずれかを入力してください。")
    print("入力が3回無効でした。申請をキャンセルします。")
    return False, "キャンセル"


def patch_human_approval_hook(auto_approve: bool = True) -> None:
    """Replace module-level approval_callback with a mock for testing/evals."""
    global approval_callback
    if auto_approve:
        approval_callback = lambda tool_name, params: (True, "OK")
    else:
        approval_callback = lambda tool_name, params: (False, "キャンセル")


class HumanApprovalHook:
    """Intercepts BeforeToolCallEvent for form-generation tools to get human approval."""

    def __init__(self, approval_callback: Callable[[str, dict], tuple[bool, str]]) -> None:
        self._approval_callback = approval_callback

    def register_hooks(self, registry: Any, **kwargs: Any) -> None:
        try:
            from strands.hooks import BeforeToolCallEvent
            registry.add_callback(BeforeToolCallEvent, self.on_before_tool_call)
        except ImportError:
            pass

    def on_before_tool_call(self, event: Any) -> None:
        tool_name = getattr(event, "tool_name", "")
        if tool_name not in _APPROVAL_TOOLS:
            return

        applicant_name = ""
        try:
            applicant_name = event.agent.context.invocation_state.get("applicant_name", "")
        except AttributeError:
            pass

        confirmation_message = self._build_confirmation_message(event, applicant_name)
        tool_input = getattr(event, "tool_input", {})
        approved, message = self._approval_callback(
            tool_name,
            {"confirmation_message": confirmation_message, "tool_params": tool_input},
        )

        result_label = "OK" if approved else message
        logger.info("[OPE-003] HumanApprovalHook介入: tool=%s, result=%s", tool_name, result_label)

        if approved:
            self._log_audit(event, "OK", applicant_name)
        else:
            self._log_audit(event, message, applicant_name)
            event.cancel_tool(message)

    def _build_confirmation_message(self, event: Any, applicant_name: str) -> str:
        tool_name = getattr(event, "tool_name", "")
        tool_input = getattr(event, "tool_input", {})

        if tool_name == "generate_transport_expense_form":
            application_date = tool_input.get("application_date", "")
            segments = tool_input.get("segments", [])
            lines = [
                "以下の申請情報をご確認ください。",
                "",
                "【交通費精算申請】",
                f"申請者: {applicant_name}",
                f"申請日: {application_date}",
            ]
            for i, seg in enumerate(segments, 1):
                lines += [
                    f"区間{i}:",
                    f"  移動日: {seg.get('travel_date', '')}  出発地: {seg.get('departure', '')}  目的地: {seg.get('destination', '')}",
                    f"  交通手段: {seg.get('transportation_type', '')}  費用: {seg.get('amount', '')}円",
                    f"  業務目的: {seg.get('purpose', '')}",
                ]
            lines += [
                "",
                "上記の内容でよろしいですか？",
                "1. OK（このまま申請書を生成する）",
                "2. 修正する",
                "3. キャンセル",
            ]
            return "\n".join(lines)

        elif tool_name == "generate_expense_reimbursement_form":
            application_date = tool_input.get("application_date", "")
            items = tool_input.get("items", [])
            lines = [
                "以下の申請情報をご確認ください。",
                "",
                "【経費精算申請】",
                f"申請者: {applicant_name}",
                f"申請日: {application_date}",
            ]
            for i, item in enumerate(items, 1):
                lines += [
                    f"経費{i}:",
                    f"  発生日: {item.get('expense_date', '')}  店舗名: {item.get('store_name', '')}  金額: {item.get('amount', '')}円",
                    f"  品目: {item.get('item_name', '')}  経費区分: {item.get('expense_category', '')}",
                    f"  業務目的: {item.get('purpose', '')}",
                ]
            lines += [
                "",
                "上記の内容でよろしいですか？",
                "1. OK（このまま申請書を生成する）",
                "2. 修正する",
                "3. キャンセル",
            ]
            return "\n".join(lines)

        return ""

    def _log_audit(self, event: Any, result: str, applicant_name: str) -> None:
        tool_name = getattr(event, "tool_name", "")
        request_id = ""
        agent_id = ""
        try:
            request_id = event.agent.context.invocation_state.get("session_id", "")
            agent_id = event.agent.name or ""
        except AttributeError:
            pass
        application_type = (
            "交通費精算申請" if tool_name == "generate_transport_expense_form" else "経費精算申請"
        )
        masked_name = (applicant_name[:1] + "***") if applicant_name else "***"
        logger.info(
            "[AUD-004] HITL確認: request_id=%s, agent_id=%s, 申請種別=%s, 結果=%s, applicant=%s",
            request_id,
            agent_id,
            application_type,
            result,
            masked_name,
        )
