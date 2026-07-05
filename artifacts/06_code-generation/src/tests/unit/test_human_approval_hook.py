"""HumanApprovalHookの単体テスト"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from unittest.mock import MagicMock
from handlers.human_approval_hook import HumanApprovalHook


def _make_event(tool_name: str, tool_params: dict = None):
    """BeforeToolCallEvent のモックを生成するヘルパー"""
    event = MagicMock()
    event.tool_use = {"name": tool_name, "input": tool_params or {}}
    event.cancel_tool = None
    return event


class TestHumanApprovalHook:
    def test_承認対象外ツールはスキップされる(self):
        callback = MagicMock()
        hook = HumanApprovalHook(approval_callback=callback)
        event = _make_event("calculate_transport_fare")
        hook._on_before_tool_call(event)
        callback.assert_not_called()
        assert event.cancel_tool is None

    def test_承認OKでcancel_toolがセットされない(self):
        callback = MagicMock(return_value=(True, ""))
        hook = HumanApprovalHook(approval_callback=callback)
        event = _make_event("generate_transport_expense_form", {"user_name": "田中"})
        hook._on_before_tool_call(event)
        callback.assert_called_once()
        assert event.cancel_tool is None

    def test_承認CANCELでキャンセルメッセージがセットされる(self):
        callback = MagicMock(return_value=(False, "CANCEL"))
        hook = HumanApprovalHook(approval_callback=callback)
        event = _make_event("generate_transport_expense_form")
        hook._on_before_tool_call(event)
        assert event.cancel_tool is not None
        assert "キャンセル" in event.cancel_tool or "中止" in event.cancel_tool

    def test_修正要望でメッセージがセットされる(self):
        callback = MagicMock(return_value=(False, "日付を修正してください"))
        hook = HumanApprovalHook(approval_callback=callback)
        event = _make_event("generate_general_expense_form")
        hook._on_before_tool_call(event)
        assert event.cancel_tool is not None
        assert "日付を修正してください" in event.cancel_tool

    def test_カスタム承認対象ツールが機能する(self):
        callback = MagicMock(return_value=(True, ""))
        hook = HumanApprovalHook(
            approval_callback=callback,
            approval_required_tools=["custom_tool"],
        )
        event = _make_event("custom_tool")
        hook._on_before_tool_call(event)
        callback.assert_called_once()

    def test_tool_useがNoneの場合スキップされる(self):
        callback = MagicMock()
        hook = HumanApprovalHook(approval_callback=callback)
        event = MagicMock()
        event.tool_use = None
        hook._on_before_tool_call(event)
        callback.assert_not_called()


class TestBuildCancelMessage:
    def test_CANCELメッセージが申請中止を含む(self):
        hook = HumanApprovalHook(approval_callback=MagicMock())
        msg = hook._build_cancel_message("test_tool", "CANCEL")
        assert "キャンセル" in msg or "中止" in msg

    def test_空文字でキャンセルメッセージを返す(self):
        hook = HumanApprovalHook(approval_callback=MagicMock())
        msg = hook._build_cancel_message("test_tool", "")
        assert len(msg) > 0

    def test_修正内容が含まれたメッセージを返す(self):
        hook = HumanApprovalHook(approval_callback=MagicMock())
        msg = hook._build_cancel_message("test_tool", "氏名を変更")
        assert "氏名を変更" in msg
