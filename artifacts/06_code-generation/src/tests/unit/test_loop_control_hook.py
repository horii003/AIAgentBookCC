"""LoopControlHook の単体テスト"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pytest
from unittest.mock import MagicMock, patch

from handlers.hooks import LoopControlHook
from handlers.exceptions import LoopLimitError


def _make_event(**kwargs):
    """テスト用イベントモック"""
    event = MagicMock()
    for k, v in kwargs.items():
        setattr(event, k, v)
    return event


class TestLoopControlHook:
    def test_BeforeInvocationでカウンタリセット(self):
        hook = LoopControlHook(max_iterations=5)
        hook._iteration_count = 3
        event = _make_event(agent_name="test_agent")
        hook._handle_before_invocation(event)
        assert hook._iteration_count == 0

    def test_AfterModelCall_exception_None_でカウントアップ(self):
        hook = LoopControlHook(max_iterations=5)
        event = _make_event(exception=None, agent_name="test")
        hook._handle_after_model_call(event)
        assert hook._iteration_count == 1

    def test_AfterModelCall_exception_有り_でカウントアップしない(self):
        hook = LoopControlHook(max_iterations=5)
        event = _make_event(exception=Exception("err"), agent_name="test")
        hook._handle_after_model_call(event)
        assert hook._iteration_count == 0

    def test_max_iterations到達でLoopLimitError送出(self):
        hook = LoopControlHook(max_iterations=3)
        event = _make_event(exception=None, agent_name="test")
        hook._handle_after_model_call(event)
        hook._handle_after_model_call(event)
        with pytest.raises(LoopLimitError) as exc_info:
            hook._handle_after_model_call(event)
        assert exc_info.value.current_iteration == 3
        assert exc_info.value.max_iterations == 3

    def test_LoopLimitErrorのフィールドが正しい(self):
        hook = LoopControlHook(max_iterations=2)
        event = _make_event(exception=None, agent_name="my_agent")
        hook._handle_after_model_call(event)
        with pytest.raises(LoopLimitError) as exc_info:
            hook._handle_after_model_call(event)
        err = exc_info.value
        assert err.max_iterations == 2
        assert err.agent_name == "my_agent"

    def test_register_hooks_6イベントを登録(self):
        hook = LoopControlHook()
        registry = MagicMock()
        hook.register_hooks(registry)
        assert registry.add_callback.call_count == 6
