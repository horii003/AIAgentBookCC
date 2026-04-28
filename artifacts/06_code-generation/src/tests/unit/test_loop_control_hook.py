"""Unit tests for hooks/loop_control_hook.py"""
import pytest
from unittest.mock import MagicMock, patch

from handlers.exceptions import LoopLimitError
from hooks.loop_control_hook import LoopControlHook


def _make_mock_event(cls_name: str, **kwargs):
    """Create a mock event with the given attributes."""
    mock = MagicMock()
    for k, v in kwargs.items():
        setattr(mock, k, v)
    return mock


class TestLoopControlHookInit:
    def test_default_max_iterations(self):
        hook = LoopControlHook()
        assert hook._max_iterations == 30

    def test_custom_max_iterations(self):
        hook = LoopControlHook(max_iterations=5)
        assert hook._max_iterations == 5

    def test_default_agent_name(self):
        hook = LoopControlHook()
        assert hook._agent_name == ""

    def test_custom_agent_name(self):
        hook = LoopControlHook(agent_name="AG-001")
        assert hook._agent_name == "AG-001"

    def test_initial_iteration_count(self):
        hook = LoopControlHook()
        assert hook._iteration_count == 0


class TestRegisterHooks:
    def test_register_hooks_adds_callbacks(self):
        hook = LoopControlHook()
        registry = MagicMock()
        hook.register_hooks(registry)
        assert registry.add_callback.call_count == 6


class TestOnBeforeInvocation:
    def test_resets_counter(self):
        hook = LoopControlHook()
        hook._iteration_count = 10
        event = _make_mock_event("BeforeInvocationEvent")
        hook._on_before_invocation(event)
        assert hook._iteration_count == 0


class TestOnAfterModelCall:
    def test_increments_counter_when_no_exception(self):
        hook = LoopControlHook(max_iterations=10)
        event = _make_mock_event("AfterModelCallEvent", exception=None)
        hook._on_after_model_call(event)
        assert hook._iteration_count == 1

    def test_skips_increment_when_exception_present(self):
        hook = LoopControlHook(max_iterations=10)
        event = _make_mock_event("AfterModelCallEvent", exception=Exception("err"))
        hook._on_after_model_call(event)
        assert hook._iteration_count == 0

    def test_raises_loop_limit_error_at_max(self):
        hook = LoopControlHook(max_iterations=3, agent_name="test_agent")
        event = _make_mock_event("AfterModelCallEvent", exception=None)
        # Simulate 3 iterations reaching the limit
        hook._iteration_count = 2
        with pytest.raises(LoopLimitError) as exc_info:
            hook._on_after_model_call(event)
        err = exc_info.value
        assert err.current_iteration == 3
        assert err.max_iterations == 3
        assert err.agent_name == "test_agent"

    def test_no_error_below_max(self):
        hook = LoopControlHook(max_iterations=5)
        event = _make_mock_event("AfterModelCallEvent", exception=None)
        hook._iteration_count = 3
        hook._on_after_model_call(event)  # Should not raise; count becomes 4
        assert hook._iteration_count == 4


class TestOnAfterInvocation:
    def test_logs_total_iterations(self):
        hook = LoopControlHook()
        hook._iteration_count = 7
        event = _make_mock_event("AfterInvocationEvent")
        with patch.object(hook._logger, "info") as mock_log:
            hook._on_after_invocation(event)
            mock_log.assert_called_once()
            log_msg = mock_log.call_args[0][0]
            assert "呼び出し完了" in log_msg or "total_iterations" in log_msg
