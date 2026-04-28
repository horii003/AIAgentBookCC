"""HumanApprovalHook の単体テスト"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pytest
from unittest.mock import MagicMock, patch, call

from handlers.hooks import HumanApprovalHook


def _make_event(tool_name: str, tool_params: dict = None):
    event = MagicMock()
    event.tool_name = tool_name
    event.tool_params = tool_params or {}
    # cancel_tool 属性は未設定
    del event.cancel_tool
    return event


class TestHumanApprovalHook:
    def test_TOOL001はスルーされる(self):
        hook = HumanApprovalHook()
        event = MagicMock()
        event.tool_name = "calculate_travel_expense"
        hook._handle_before_tool_call(event)
        # cancel_tool が設定されていないこと
        assert not hasattr(event, "cancel_tool") or event.cancel_tool != "申請をキャンセルしました。"

    def test_TOOL002はブロックされる(self):
        hook = HumanApprovalHook()
        with patch.object(hook, "_request_approval", return_value=(True, "")) as mock_req:
            event = MagicMock()
            event.tool_name = "generate_travel_expense_form"
            event.tool_params = {}
            hook._handle_before_tool_call(event)
            mock_req.assert_called_once()

    def test_ok入力でTrue空文字返却(self):
        hook = HumanApprovalHook()
        with patch("builtins.input", return_value="ok"):
            result = hook._request_approval("generate_travel_expense_form", {})
        assert result == (True, "")

    def test_修正入力で修正内容返却(self):
        hook = HumanApprovalHook()
        inputs = iter(["修正", "金額を10000円に変更"])
        with patch("builtins.input", side_effect=inputs):
            result = hook._request_approval("generate_travel_expense_form", {})
        assert result[0] is False
        assert result[1] == "金額を10000円に変更"

    def test_キャンセル入力でCANCEL返却(self):
        hook = HumanApprovalHook()
        with patch("builtins.input", return_value="キャンセル"):
            result = hook._request_approval("generate_travel_expense_form", {})
        assert result == (False, "CANCEL")

    def test_無効入力後にok入力でTrue返却(self):
        hook = HumanApprovalHook()
        inputs = iter(["yes", "no", "ok"])
        with patch("builtins.input", side_effect=inputs):
            result = hook._request_approval("generate_travel_expense_form", {})
        assert result == (True, "")

    def test_EOFErrorでCANCEL返却(self):
        hook = HumanApprovalHook()
        with patch("builtins.input", side_effect=EOFError):
            result = hook._request_approval("generate_travel_expense_form", {})
        assert result == (False, "CANCEL")

    def test_ok時はcancel_toolが設定されない(self):
        hook = HumanApprovalHook()
        with patch.object(hook, "_request_approval", return_value=(True, "")):
            event = MagicMock(spec=[])
            event.tool_name = "generate_travel_expense_form"
            event.tool_params = {}
            hook._handle_before_tool_call(event)
            assert not hasattr(event, "cancel_tool")

    def test_キャンセル時はcancel_toolに申請キャンセルメッセージ(self):
        hook = HumanApprovalHook()
        with patch.object(hook, "_request_approval", return_value=(False, "CANCEL")):
            event = MagicMock()
            event.tool_name = "generate_travel_expense_form"
            event.tool_params = {}
            hook._handle_before_tool_call(event)
            assert event.cancel_tool == "申請をキャンセルしました。"

    def test_修正時はcancel_toolに修正内容がセット(self):
        hook = HumanApprovalHook()
        with patch.object(hook, "_request_approval", return_value=(False, "金額修正")):
            event = MagicMock()
            event.tool_name = "generate_expense_form"
            event.tool_params = {}
            hook._handle_before_tool_call(event)
            assert event.cancel_tool == "金額修正"

    def test_register_hooks_BeforeToolCallEventのみ登録(self):
        hook = HumanApprovalHook()
        registry = MagicMock()
        hook.register_hooks(registry)
        assert registry.add_callback.call_count == 1
