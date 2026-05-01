"""loop_control_hook.py の単体テスト"""
import pytest
from unittest.mock import MagicMock

from handlers.loop_control_hook import LoopControlHook, LoopLimitError


def _make_event(event_cls, **kwargs):
    """テスト用イベントオブジェクトを生成する。"""
    event = MagicMock(spec=event_cls)
    for k, v in kwargs.items():
        setattr(event, k, v)
    return event


class TestLoopLimitError:
    def test_fields(self):
        """LoopLimitError が正しいフィールドを保持すること"""
        err = LoopLimitError(current_iteration=10, max_iterations=10, agent_name="AG-001")
        assert err.current_iteration == 10
        assert err.max_iterations == 10
        assert err.agent_name == "AG-001"

    def test_message_contains_info(self):
        """LoopLimitError のメッセージにエージェント名とループ回数が含まれること"""
        err = LoopLimitError(current_iteration=5, max_iterations=10, agent_name="TestAgent")
        msg = str(err)
        assert "TestAgent" in msg
        assert "10" in msg


class TestLoopControlHook:
    def _make_hook(self, max_iterations=10, agent_name="TestAgent"):
        return LoopControlHook(max_iterations=max_iterations, agent_name=agent_name)

    def _fire_before_invocation(self, hook):
        from strands.hooks import BeforeInvocationEvent
        event = _make_event(BeforeInvocationEvent)
        hook._before_invocation_handler(event)

    def _fire_after_model_call(self, hook, exception=None):
        from strands.hooks import AfterModelCallEvent
        event = _make_event(AfterModelCallEvent, exception=exception)
        hook._after_model_call_handler(event)

    def _fire_after_invocation(self, hook):
        from strands.hooks import AfterInvocationEvent
        event = _make_event(AfterInvocationEvent)
        hook._after_invocation_handler(event)

    def test_before_invocation_resets_counter(self):
        """BeforeInvocationEvent でカウンターが0にリセットされること"""
        hook = self._make_hook()
        hook._loop_count = 5
        self._fire_before_invocation(hook)
        assert hook._loop_count == 0

    def test_9_after_model_calls_no_error(self):
        """max_iterations=10 で9回AfterModelCallEvent後に停止しないこと"""
        hook = self._make_hook(max_iterations=10)
        self._fire_before_invocation(hook)
        for _ in range(9):
            self._fire_after_model_call(hook)
        assert hook._loop_count == 9

    def test_10th_after_model_call_raises_loop_limit_error(self):
        """max_iterations=10 で10回目に LoopLimitError が発生すること"""
        hook = self._make_hook(max_iterations=10)
        self._fire_before_invocation(hook)
        for _ in range(9):
            self._fire_after_model_call(hook)
        with pytest.raises(LoopLimitError) as exc_info:
            self._fire_after_model_call(hook)
        assert exc_info.value.current_iteration == 10
        assert exc_info.value.max_iterations == 10

    def test_max_iterations_1_raises_on_first_call(self):
        """max_iterations=1 で1回目に LoopLimitError が発生すること"""
        hook = self._make_hook(max_iterations=1)
        self._fire_before_invocation(hook)
        with pytest.raises(LoopLimitError):
            self._fire_after_model_call(hook)

    def test_after_invocation_does_not_reset_counter(self):
        """AfterInvocationEvent でカウンターがリセットされないこと"""
        hook = self._make_hook(max_iterations=10)
        self._fire_before_invocation(hook)
        for _ in range(3):
            self._fire_after_model_call(hook)
        self._fire_after_invocation(hook)
        assert hook._loop_count == 3

    def test_exception_in_event_skips_count(self):
        """event.exception 存在時にカウントアップされないこと"""
        hook = self._make_hook(max_iterations=10)
        self._fire_before_invocation(hook)
        self._fire_after_model_call(hook, exception=Exception("API error"))
        assert hook._loop_count == 0

    def test_before_invocation_resets_after_previous_run(self):
        """再呼び出し時に前回のカウントがリセットされること"""
        hook = self._make_hook(max_iterations=10)
        self._fire_before_invocation(hook)
        for _ in range(5):
            self._fire_after_model_call(hook)
        assert hook._loop_count == 5
        self._fire_before_invocation(hook)
        assert hook._loop_count == 0
