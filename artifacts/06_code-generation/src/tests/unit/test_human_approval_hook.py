"""human_approval_hook.py の単体テスト"""
import pytest
from unittest.mock import MagicMock, patch

from handlers.human_approval_hook import HumanApprovalHook, APPROVAL_TOOL_NAMES


def _make_event(tool_name, tool_params=None):
    """テスト用 BeforeToolCallEvent を生成する。"""
    from strands.hooks import BeforeToolCallEvent
    event = MagicMock(spec=BeforeToolCallEvent)
    event.tool_name = tool_name
    event.tool_use = {"input": tool_params or {}}
    event.cancel_tool = None
    return event


class TestHumanApprovalHook:
    def test_non_target_tool_skips(self):
        """承認対象外ツールのときコールバックが呼び出されないこと"""
        callback = MagicMock()
        hook = HumanApprovalHook(approval_callback=callback)
        event = _make_event("calculate_transport_fare")
        hook._before_tool_call_handler(event)
        callback.assert_not_called()
        assert event.cancel_tool is None

    def test_ok_approval_continues_tool(self):
        """'OK' 入力でツール実行が継続されること（cancel_tool が設定されないこと）"""
        callback = MagicMock(return_value=(True, ""))
        hook = HumanApprovalHook(approval_callback=callback)
        event = _make_event("generate_transport_application")
        with patch.object(hook, "_write_audit_log"):
            hook._before_tool_call_handler(event)
        assert event.cancel_tool is None

    def test_modify_sets_cancel_tool(self):
        """'修正' 入力で event.cancel_tool がセットされること"""
        callback = MagicMock(return_value=(False, "交通手段を変更してください"))
        hook = HumanApprovalHook(approval_callback=callback)
        event = _make_event("generate_transport_application")
        hook._before_tool_call_handler(event)
        assert "修正要求" in event.cancel_tool
        assert "交通手段を変更してください" in event.cancel_tool

    def test_cancel_sets_cancel_tool(self):
        """'キャンセル' 入力で event.cancel_tool が 'キャンセル' に設定されること"""
        callback = MagicMock(return_value=(False, "CANCEL"))
        hook = HumanApprovalHook(approval_callback=callback)
        event = _make_event("generate_expense_application")
        with patch.object(hook, "_write_audit_log"):
            hook._before_tool_call_handler(event)
        assert event.cancel_tool == "キャンセル"

    def test_3_invalid_inputs_causes_cancel(self):
        """認識不能入力が3回続いた場合にキャンセル扱いとなること"""
        # 空文字列の detail を返し続ける（不正扱い）
        callback = MagicMock(return_value=(False, ""))
        hook = HumanApprovalHook(approval_callback=callback)
        event = _make_event("generate_transport_application")
        with patch.object(hook, "_write_audit_log"):
            hook._before_tool_call_handler(event)
        assert event.cancel_tool == "キャンセル"
        assert callback.call_count == 3

    def test_expense_application_is_target(self):
        """generate_expense_application も承認対象であること"""
        callback = MagicMock(return_value=(True, ""))
        hook = HumanApprovalHook(approval_callback=callback)
        event = _make_event("generate_expense_application")
        with patch.object(hook, "_write_audit_log"):
            hook._before_tool_call_handler(event)
        callback.assert_called_once()
