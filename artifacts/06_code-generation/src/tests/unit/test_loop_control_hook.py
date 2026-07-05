"""LoopControlHookの単体テスト"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from unittest.mock import MagicMock, patch
from handlers.loop_control_hook import LoopControlHook
from handlers.error_handler import LoopLimitError


def _make_model_event(exception=None):
    event = MagicMock()
    event.exception = exception
    return event


def _make_tool_event(tool_name: str = "test_tool"):
    event = MagicMock()
    event.tool_use = {"name": tool_name}
    return event


class TestLoopControlHook:
    def test_初期化でiteration_countが0(self):
        hook = LoopControlHook(max_iterations=10, agent_name="test_agent")
        assert hook.iteration_count == 0
        assert hook.max_iterations == 10
        assert hook.agent_name == "test_agent"

    def test_before_invocationでカウントが0にリセットされる(self):
        hook = LoopControlHook(max_iterations=5)
        hook.iteration_count = 3
        event = MagicMock()
        hook.on_before_invocation(event)
        assert hook.iteration_count == 0

    def test_after_model_callでカウントがインクリメントされる(self):
        hook = LoopControlHook(max_iterations=10)
        hook.on_after_model_call(_make_model_event())
        assert hook.iteration_count == 1

    def test_max_iterations超過でLoopLimitErrorが発生する(self):
        hook = LoopControlHook(max_iterations=3, agent_name="test")
        hook.iteration_count = 3
        with pytest.raises(LoopLimitError):
            hook.on_after_model_call(_make_model_event())

    def test_例外ありのafter_model_callはカウントをスキップする(self):
        hook = LoopControlHook(max_iterations=10)
        hook.on_after_model_call(_make_model_event(exception=Exception("error")))
        assert hook.iteration_count == 0

    def test_LoopLimitErrorにエージェント名とループ回数が含まれる(self):
        hook = LoopControlHook(max_iterations=3, agent_name="my_agent")
        hook.iteration_count = 3
        with pytest.raises(LoopLimitError) as exc_info:
            hook.on_after_model_call(_make_model_event())
        error = exc_info.value
        assert error.agent_name == "my_agent"
        assert error.max_iterations == 3

    def test_tool_useがNoneでもon_before_tool_callが動作する(self):
        hook = LoopControlHook()
        event = MagicMock()
        event.tool_use = None
        hook.on_before_tool_call(event)

    def test_after_invocationでログが出力される(self):
        hook = LoopControlHook(max_iterations=10, agent_name="ag")
        hook.iteration_count = 2
        with patch("handlers.loop_control_hook._logger") as mock_logger:
            hook.on_after_invocation(MagicMock())
            mock_logger.info.assert_called()


class TestGetToolName:
    def test_tool_useがある場合ツール名を返す(self):
        hook = LoopControlHook()
        event = MagicMock()
        event.tool_use = {"name": "my_tool"}
        assert hook._get_tool_name(event) == "my_tool"

    def test_tool_useがNoneでunknownを返す(self):
        hook = LoopControlHook()
        event = MagicMock()
        event.tool_use = None
        assert hook._get_tool_name(event) == "unknown"
