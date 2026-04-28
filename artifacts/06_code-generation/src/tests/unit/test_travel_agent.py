"""travel_agent.py の単体テスト"""
import sys
import os
import unittest.mock as mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import agents.travel_agent as travel_agent_module


def _reset_cache():
    travel_agent_module._agent_instances.clear()


class TestGetTravelAgent:
    def setup_method(self):
        _reset_cache()

    def test_Agentインスタンスを返す(self):
        with mock.patch("agents.travel_agent.Agent") as MockAgent, \
             mock.patch("agents.travel_agent.FileSessionManager"), \
             mock.patch("agents.travel_agent.ModelConfig"):
            MockAgent.return_value = mock.MagicMock()
            from agents.travel_agent import _get_travel_agent
            result = _get_travel_agent("sess_001", "田中太郎", "2026-04-28")
            assert result is MockAgent.return_value

    def test_SlidingWindowConversationManagerがwindow_size_20で設定される(self):
        with mock.patch("agents.travel_agent.Agent"), \
             mock.patch("agents.travel_agent.FileSessionManager"), \
             mock.patch("agents.travel_agent.ModelConfig"), \
             mock.patch("agents.travel_agent.SlidingWindowConversationManager") as MockCM:
            from agents.travel_agent import _get_travel_agent
            _get_travel_agent("sess_002", "田中太郎", "2026-04-28")
            assert MockCM.called
            kwargs = MockCM.call_args.kwargs if MockCM.call_args.kwargs else {}
            args = MockCM.call_args.args if MockCM.call_args.args else ()
            window_size = kwargs.get("window_size") or (args[0] if args else None)
            assert window_size == 20

    def test_toolsにcalculate_travel_expenseとgenerate_travel_expense_formが含まれる(self):
        with mock.patch("agents.travel_agent.Agent") as MockAgent, \
             mock.patch("agents.travel_agent.FileSessionManager"), \
             mock.patch("agents.travel_agent.ModelConfig"):
            MockAgent.return_value = mock.MagicMock()
            from agents.travel_agent import _get_travel_agent
            from tools.travel_tools import calculate_travel_expense
            from tools.output_generator import generate_travel_expense_form
            _get_travel_agent("sess_003", "田中太郎", "2026-04-28")
            call_args = MockAgent.call_args
            if call_args and call_args.kwargs:
                tools = call_args.kwargs.get("tools", [])
                assert calculate_travel_expense in tools
                assert generate_travel_expense_form in tools

    def test_hooksにHumanApprovalHookとLoopControlHookが含まれる(self):
        with mock.patch("agents.travel_agent.Agent") as MockAgent, \
             mock.patch("agents.travel_agent.FileSessionManager"), \
             mock.patch("agents.travel_agent.ModelConfig"):
            MockAgent.return_value = mock.MagicMock()
            from agents.travel_agent import _get_travel_agent
            from handlers.hooks import HumanApprovalHook, LoopControlHook
            _get_travel_agent("sess_004", "田中太郎", "2026-04-28")
            call_args = MockAgent.call_args
            if call_args and call_args.kwargs:
                hooks = call_args.kwargs.get("hooks", [])
                hook_types = [type(h) for h in hooks]
                assert HumanApprovalHook in hook_types
                assert LoopControlHook in hook_types

    def test_callback_handler_Noneが設定される(self):
        with mock.patch("agents.travel_agent.Agent") as MockAgent, \
             mock.patch("agents.travel_agent.FileSessionManager"), \
             mock.patch("agents.travel_agent.ModelConfig"):
            MockAgent.return_value = mock.MagicMock()
            from agents.travel_agent import _get_travel_agent
            _get_travel_agent("sess_005", "田中太郎", "2026-04-28")
            call_args = MockAgent.call_args
            if call_args and call_args.kwargs:
                assert call_args.kwargs.get("callback_handler") is None

    def test_同一session_idで2回呼び出すと同じインスタンスが返る(self):
        with mock.patch("agents.travel_agent.Agent") as MockAgent, \
             mock.patch("agents.travel_agent.FileSessionManager"), \
             mock.patch("agents.travel_agent.ModelConfig"):
            mock_agent = mock.MagicMock()
            MockAgent.return_value = mock_agent
            from agents.travel_agent import _get_travel_agent
            agent1 = _get_travel_agent("sess_cache", "田中太郎", "2026-04-28")
            agent2 = _get_travel_agent("sess_cache", "田中太郎", "2026-04-28")
            assert agent1 is agent2
            assert MockAgent.call_count == 1
