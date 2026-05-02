import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from unittest.mock import MagicMock

from handlers.loop_control_hook import LoopControlHook, LoopLimitError


def make_model_event(exception=None):
    event = MagicMock()
    event.exception = exception
    event.agent.name = "test_agent"
    return event


def make_invocation_event():
    return MagicMock()


class TestLoopLimitError:
    def test_attributes(self):
        err = LoopLimitError(11, 10, "my_agent")
        assert err.current_iteration == 11
        assert err.max_iterations == 10
        assert err.agent_name == "my_agent"

    def test_is_runtime_error(self):
        err = LoopLimitError(11, 10)
        assert isinstance(err, RuntimeError)


class TestLoopControlHook:
    def test_counter_resets_on_invocation(self):
        hook = LoopControlHook(max_iterations=10)
        hook._iteration_count = 5
        hook.on_before_invocation(make_invocation_event())
        assert hook._iteration_count == 0

    def test_raises_loop_limit_error_after_max(self):
        hook = LoopControlHook(max_iterations=3)
        event = make_model_event()
        hook.on_before_model_call(event)
        hook.on_before_model_call(event)
        hook.on_before_model_call(event)
        with pytest.raises(LoopLimitError) as exc_info:
            hook.on_before_model_call(event)
        assert exc_info.value.current_iteration == 4
        assert exc_info.value.max_iterations == 3

    def test_does_not_raise_at_max(self):
        hook = LoopControlHook(max_iterations=3)
        event = make_model_event()
        for _ in range(3):
            hook.on_before_model_call(event)
        # exactly at max should not raise

    def test_after_model_call_decrements_on_exception(self):
        hook = LoopControlHook(max_iterations=10)
        hook._iteration_count = 3
        event = make_model_event(exception=Exception("err"))
        hook.on_after_model_call(event)
        assert hook._iteration_count == 2

    def test_after_model_call_no_decrement_when_no_exception(self):
        hook = LoopControlHook(max_iterations=10)
        hook._iteration_count = 3
        event = make_model_event(exception=None)
        hook.on_after_model_call(event)
        assert hook._iteration_count == 3

    def test_before_tool_call_no_error(self):
        hook = LoopControlHook()
        event = MagicMock()
        event.tool_name = "some_tool"
        hook.on_before_tool_call(event)  # should not raise

    def test_after_tool_call_no_error(self):
        hook = LoopControlHook()
        event = MagicMock()
        event.tool_name = "some_tool"
        hook.on_after_tool_call(event)  # should not raise
