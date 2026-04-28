"""Unit tests for hooks/human_approval_hook.py"""
import pytest
from unittest.mock import MagicMock, patch

from hooks.human_approval_hook import HumanApprovalHook, _normalize_input


# ---- _normalize_input ----

class TestNormalizeInput:
    def test_ok_upper(self):
        assert _normalize_input("OK") == "OK"

    def test_ok_lower(self):
        assert _normalize_input("ok") == "OK"

    def test_ok_number(self):
        assert _normalize_input("1") == "OK"

    def test_ok_hai(self):
        assert _normalize_input("はい") == "OK"

    def test_shyuusei(self):
        assert _normalize_input("修正") == "修正"

    def test_shyuusei_number(self):
        assert _normalize_input("2") == "修正"

    def test_cancel_katakana(self):
        assert _normalize_input("キャンセル") == "キャンセル"

    def test_cancel_english(self):
        assert _normalize_input("cancel") == "キャンセル"

    def test_cancel_number(self):
        assert _normalize_input("3") == "キャンセル"

    def test_invalid_returns_none(self):
        assert _normalize_input("abc") is None

    def test_empty_returns_none(self):
        assert _normalize_input("") is None


# ---- HumanApprovalHook ----

def _make_tool_use_dict(tool_name: str, params: dict = None):
    """Create a mock tool_use object with dict-like access."""
    d = {"name": tool_name, "input": params or {}}
    mock = MagicMock()
    mock.get = lambda k, default=None: d.get(k, default)
    mock.__getitem__ = lambda self, k: d[k]
    return mock


def _make_event(tool_name: str, tool_params: dict = None):
    event = MagicMock()
    event.tool_use = _make_tool_use_dict(tool_name, tool_params)
    event.cancel_tool = False
    return event


class TestHumanApprovalHookInit:
    def test_stores_tool_names(self):
        hook = HumanApprovalHook(tool_names=["generate_transport_expense_form"])
        assert hook._tool_names == ["generate_transport_expense_form"]

    def test_default_callback_none(self):
        hook = HumanApprovalHook(tool_names=[])
        assert hook._approval_callback is None

    def test_custom_callback_stored(self):
        cb = lambda name, params: (True, "")
        hook = HumanApprovalHook(tool_names=[], approval_callback=cb)
        assert hook._approval_callback is cb


class TestRegisterHooks:
    def test_registers_before_tool_call(self):
        hook = HumanApprovalHook(tool_names=[])
        registry = MagicMock()
        hook.register_hooks(registry)
        registry.add_callback.assert_called_once()


class TestOnBeforeToolCallPassthrough:
    def test_non_target_tool_passes_through(self):
        hook = HumanApprovalHook(tool_names=["generate_transport_expense_form"])
        event = _make_event("calculate_transport_expense")
        hook._on_before_tool_call(event)
        assert event.cancel_tool is False


class TestOnBeforeToolCallWithCallback:
    def test_callback_approved(self):
        cb = MagicMock(return_value=(True, ""))
        hook = HumanApprovalHook(
            tool_names=["generate_transport_expense_form"],
            approval_callback=cb,
        )
        event = _make_event("generate_transport_expense_form")
        hook._on_before_tool_call(event)
        assert event.cancel_tool is False
        cb.assert_called_once()

    def test_callback_cancel(self):
        cb = MagicMock(return_value=(False, "CANCEL"))
        hook = HumanApprovalHook(
            tool_names=["generate_transport_expense_form"],
            approval_callback=cb,
        )
        event = _make_event("generate_transport_expense_form")
        hook._on_before_tool_call(event)
        assert event.cancel_tool == "申請をキャンセルしました。"

    def test_callback_modification(self):
        cb = MagicMock(return_value=(False, "日付を修正してください"))
        hook = HumanApprovalHook(
            tool_names=["generate_transport_expense_form"],
            approval_callback=cb,
        )
        event = _make_event("generate_transport_expense_form")
        hook._on_before_tool_call(event)
        assert "修正要望" in event.cancel_tool
        assert "日付を修正してください" in event.cancel_tool

    def test_callback_exception_cancels_tool(self):
        def bad_cb(name, params):
            raise RuntimeError("callback error")

        hook = HumanApprovalHook(
            tool_names=["generate_transport_expense_form"],
            approval_callback=bad_cb,
        )
        event = _make_event("generate_transport_expense_form")
        hook._on_before_tool_call(event)
        assert event.cancel_tool  # Should be set to an error message


class TestLogApproval:
    def test_log_approval_ok(self):
        hook = HumanApprovalHook(tool_names=[])
        with patch.object(hook._approval_logger, "info") as mock_log:
            hook._log_approval("generate_transport_expense_form", "OK")
            mock_log.assert_called_once()
            logged = mock_log.call_args[0][0]
            import json
            record = json.loads(logged)
            assert record["tool_name"] == "generate_transport_expense_form"
            assert record["choice"] == "OK"
            assert "timestamp" in record

    def test_log_approval_failure_does_not_raise(self):
        hook = HumanApprovalHook(tool_names=[])
        with patch.object(hook._approval_logger, "info", side_effect=Exception("log error")):
            hook._log_approval("tool", "OK")  # Should not raise
