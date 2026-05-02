import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import logging
from unittest.mock import MagicMock, patch

from handlers.human_approval_hook import HumanApprovalHook, patch_human_approval_hook


def make_event(tool_name: str, tool_input: dict = None, applicant_name: str = "田中太郎"):
    event = MagicMock()
    event.tool_name = tool_name
    event.tool_input = tool_input or {}
    event.agent.context.invocation_state = {"applicant_name": applicant_name, "session_id": "test_session"}
    event.agent.name = "test_agent"
    return event


class TestHumanApprovalHook:
    def test_approved_does_not_cancel(self):
        callback = lambda tool_name, params: (True, "OK")
        hook = HumanApprovalHook(approval_callback=callback)
        event = make_event("generate_transport_expense_form", {"application_date": "2026-05-02", "segments": []})
        hook.on_before_tool_call(event)
        event.cancel_tool.assert_not_called()

    def test_rejected_calls_cancel_tool(self):
        callback = lambda tool_name, params: (False, "修正")
        hook = HumanApprovalHook(approval_callback=callback)
        event = make_event("generate_transport_expense_form", {"application_date": "2026-05-02", "segments": []})
        hook.on_before_tool_call(event)
        event.cancel_tool.assert_called_once_with("修正")

    def test_non_target_tool_skipped(self):
        called = []
        callback = lambda tool_name, params: called.append(tool_name) or (True, "OK")
        hook = HumanApprovalHook(approval_callback=callback)
        event = make_event("calculate_transport_fare")
        hook.on_before_tool_call(event)
        assert len(called) == 0
        event.cancel_tool.assert_not_called()

    def test_expense_tool_approved(self):
        callback = lambda tool_name, params: (True, "OK")
        hook = HumanApprovalHook(approval_callback=callback)
        event = make_event("generate_expense_reimbursement_form", {"application_date": "2026-05-02", "items": []})
        hook.on_before_tool_call(event)
        event.cancel_tool.assert_not_called()

    def test_aud004_log_masks_applicant_name(self, caplog):
        callback = lambda tool_name, params: (True, "OK")
        hook = HumanApprovalHook(approval_callback=callback)
        event = make_event("generate_transport_expense_form", {}, applicant_name="田中太郎")
        with caplog.at_level(logging.INFO, logger="handlers.human_approval_hook"):
            hook.on_before_tool_call(event)
        assert "田***" in caplog.text
        assert "田中太郎" not in caplog.text

    def test_patch_human_approval_hook_auto_approve(self):
        import handlers.human_approval_hook as mod
        patch_human_approval_hook(auto_approve=True)
        approved, msg = mod.approval_callback("any_tool", {})
        assert approved is True

    def test_patch_human_approval_hook_auto_cancel(self):
        import handlers.human_approval_hook as mod
        patch_human_approval_hook(auto_approve=False)
        approved, msg = mod.approval_callback("any_tool", {})
        assert approved is False
