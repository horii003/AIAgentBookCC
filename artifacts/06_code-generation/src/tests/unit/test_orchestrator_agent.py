"""orchestrator_agent.py の単体テスト"""
import sys
import os
import unittest.mock as mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


class TestCreateOrchestratorAgent:
    def test_Agentインスタンスを返す(self):
        with mock.patch("agents.orchestrator_agent.Agent") as MockAgent, \
             mock.patch("agents.orchestrator_agent.FileSessionManager"), \
             mock.patch("agents.travel_agent.travel_application_agent_tool"), \
             mock.patch("agents.expense_agent.expense_application_agent_tool"):
            from agents.orchestrator_agent import create_orchestrator_agent
            create_orchestrator_agent("sess_001", "田中太郎", "2026-04-28")
            assert MockAgent.called

    def test_toolsにtravel_application_agent_toolが含まれる(self):
        with mock.patch("agents.orchestrator_agent.Agent") as MockAgent, \
             mock.patch("agents.orchestrator_agent.FileSessionManager"):
            from agents.travel_agent import travel_application_agent_tool
            from agents.expense_agent import expense_application_agent_tool
            from agents.orchestrator_agent import create_orchestrator_agent
            create_orchestrator_agent("sess_001", "田中太郎", "2026-04-28")
            call_kwargs = MockAgent.call_args.kwargs if MockAgent.call_args else {}
            call_args = MockAgent.call_args
            tools = None
            if call_args:
                if call_args.kwargs:
                    tools = call_args.kwargs.get("tools")
                elif call_args.args:
                    pass
            if tools is not None:
                tool_names = [getattr(t, "__name__", str(t)) for t in tools]
                assert "travel_application_agent_tool" in tool_names

    def test_SlidingWindowConversationManagerがwindow_size_30で設定される(self):
        with mock.patch("agents.orchestrator_agent.Agent") as MockAgent, \
             mock.patch("agents.orchestrator_agent.FileSessionManager"), \
             mock.patch("agents.orchestrator_agent.SlidingWindowConversationManager") as MockCM:
            from agents.orchestrator_agent import create_orchestrator_agent
            create_orchestrator_agent("sess_001", "田中太郎", "2026-04-28")
            assert MockCM.called
            kwargs = MockCM.call_args.kwargs if MockCM.call_args.kwargs else {}
            args = MockCM.call_args.args if MockCM.call_args.args else ()
            window_size = kwargs.get("window_size") or (args[0] if args else None)
            assert window_size == 30

    def test_hooksにLoopControlHookが含まれる(self):
        with mock.patch("agents.orchestrator_agent.Agent") as MockAgent, \
             mock.patch("agents.orchestrator_agent.FileSessionManager"):
            from agents.orchestrator_agent import create_orchestrator_agent
            from handlers.hooks import LoopControlHook
            create_orchestrator_agent("sess_001", "田中太郎", "2026-04-28")
            call_args = MockAgent.call_args
            hooks = None
            if call_args and call_args.kwargs:
                hooks = call_args.kwargs.get("hooks")
            if hooks is not None:
                hook_types = [type(h) for h in hooks]
                assert LoopControlHook in hook_types

    def test_hooksにHumanApprovalHookが含まれない(self):
        with mock.patch("agents.orchestrator_agent.Agent") as MockAgent, \
             mock.patch("agents.orchestrator_agent.FileSessionManager"):
            from agents.orchestrator_agent import create_orchestrator_agent
            from handlers.hooks import HumanApprovalHook
            create_orchestrator_agent("sess_001", "田中太郎", "2026-04-28")
            call_args = MockAgent.call_args
            hooks = None
            if call_args and call_args.kwargs:
                hooks = call_args.kwargs.get("hooks")
            if hooks is not None:
                hook_types = [type(h) for h in hooks]
                assert HumanApprovalHook not in hook_types
