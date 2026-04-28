"""Unit tests for agents/expense_agent.py"""
import pytest
from unittest.mock import MagicMock, patch


class TestExpenseAgentFactory:
    def setup_method(self):
        from agents.expense_agent import ExpenseAgentFactory
        ExpenseAgentFactory._instances.clear()

    def teardown_method(self):
        from agents.expense_agent import ExpenseAgentFactory
        ExpenseAgentFactory._instances.clear()

    def test_get_agent_returns_agent_instance(self):
        from agents.expense_agent import ExpenseAgentFactory
        from strands import Agent

        mock_agent = MagicMock(spec=Agent)
        with patch("agents.expense_agent.Agent", return_value=mock_agent):
            with patch("agents.expense_agent.FileSessionManager"):
                agent = ExpenseAgentFactory.get_agent("sess-001", "2026-04-28")

        assert agent is mock_agent

    def test_get_agent_caches_same_session(self):
        from agents.expense_agent import ExpenseAgentFactory

        call_count = 0
        def make_agent(**kwargs):
            nonlocal call_count
            call_count += 1
            return MagicMock()

        with patch("agents.expense_agent.Agent", side_effect=make_agent):
            with patch("agents.expense_agent.FileSessionManager"):
                agent1 = ExpenseAgentFactory.get_agent("sess-exp", "2026-04-28")
                agent2 = ExpenseAgentFactory.get_agent("sess-exp", "2026-04-28")

        assert agent1 is agent2
        assert call_count == 1

    def test_remove_clears_session(self):
        from agents.expense_agent import ExpenseAgentFactory

        with patch("agents.expense_agent.Agent", return_value=MagicMock()):
            with patch("agents.expense_agent.FileSessionManager"):
                ExpenseAgentFactory.get_agent("sess-del", "2026-04-28")

        assert "sess-del" in ExpenseAgentFactory._instances
        ExpenseAgentFactory.remove("sess-del")
        assert "sess-del" not in ExpenseAgentFactory._instances

    def test_agent_has_sliding_window_size_15(self):
        from agents.expense_agent import ExpenseAgentFactory
        from strands.agent.conversation_manager import SlidingWindowConversationManager

        captured = {}
        def capture(**kwargs):
            captured.update(kwargs)
            return MagicMock()

        with patch("agents.expense_agent.Agent", side_effect=capture):
            with patch("agents.expense_agent.FileSessionManager"):
                ExpenseAgentFactory.get_agent("sess-win", "2026-04-28")

        conv_mgr = captured.get("conversation_manager")
        assert isinstance(conv_mgr, SlidingWindowConversationManager)

    def test_agent_tools_contain_generate_expense_form(self):
        from agents.expense_agent import ExpenseAgentFactory
        from tools.output_generator import generate_expense_form

        captured = {}
        def capture(**kwargs):
            captured.update(kwargs)
            return MagicMock()

        with patch("agents.expense_agent.Agent", side_effect=capture):
            with patch("agents.expense_agent.FileSessionManager"):
                ExpenseAgentFactory.get_agent("sess-tools", "2026-04-28")

        tools = captured.get("tools", [])
        tool_names = [getattr(t, "__name__", str(t)) for t in tools]
        assert "generate_expense_form" in tool_names

    def test_agent_tools_do_not_contain_calculate_transport(self):
        from agents.expense_agent import ExpenseAgentFactory

        captured = {}
        def capture(**kwargs):
            captured.update(kwargs)
            return MagicMock()

        with patch("agents.expense_agent.Agent", side_effect=capture):
            with patch("agents.expense_agent.FileSessionManager"):
                ExpenseAgentFactory.get_agent("sess-tools2", "2026-04-28")

        tools = captured.get("tools", [])
        tool_names = [getattr(t, "__name__", str(t)) for t in tools]
        assert "calculate_transport_expense" not in tool_names

    def test_agent_has_human_approval_hook(self):
        from agents.expense_agent import ExpenseAgentFactory
        from hooks.human_approval_hook import HumanApprovalHook

        captured = {}
        def capture(**kwargs):
            captured.update(kwargs)
            return MagicMock()

        with patch("agents.expense_agent.Agent", side_effect=capture):
            with patch("agents.expense_agent.FileSessionManager"):
                ExpenseAgentFactory.get_agent("sess-hook", "2026-04-28")

        hooks = captured.get("hooks", [])
        assert any(isinstance(h, HumanApprovalHook) for h in hooks)

    def test_agent_has_loop_control_hook_max_30(self):
        from agents.expense_agent import ExpenseAgentFactory
        from hooks.loop_control_hook import LoopControlHook

        captured = {}
        def capture(**kwargs):
            captured.update(kwargs)
            return MagicMock()

        with patch("agents.expense_agent.Agent", side_effect=capture):
            with patch("agents.expense_agent.FileSessionManager"):
                ExpenseAgentFactory.get_agent("sess-loop", "2026-04-28")

        hooks = captured.get("hooks", [])
        loop_hooks = [h for h in hooks if isinstance(h, LoopControlHook)]
        assert len(loop_hooks) > 0
        assert loop_hooks[0]._max_iterations == 30

    def test_agent_callback_handler_none(self):
        from agents.expense_agent import ExpenseAgentFactory

        captured = {}
        def capture(**kwargs):
            captured.update(kwargs)
            return MagicMock()

        with patch("agents.expense_agent.Agent", side_effect=capture):
            with patch("agents.expense_agent.FileSessionManager"):
                ExpenseAgentFactory.get_agent("sess-cb", "2026-04-28")

        assert captured.get("callback_handler") is None


class TestExpenseApplicationAgentTool:
    def _make_context(self, session_id="sess-test", applicant_name="田中花子", application_date="2026-04-28"):
        ctx = MagicMock()
        ctx.invocation_state = {
            "session_id": session_id,
            "applicant_name": applicant_name,
            "application_date": application_date,
        }
        return ctx

    def setup_method(self):
        from agents.expense_agent import ExpenseAgentFactory
        ExpenseAgentFactory._instances.clear()

    def test_missing_applicant_name_returns_error(self):
        from agents.expense_agent import expense_application_agent_tool
        ctx = self._make_context(applicant_name="")
        result = expense_application_agent_tool(query="経費申請", tool_context=ctx)
        assert "エラー" in result

    def test_invalid_date_returns_error(self):
        from agents.expense_agent import expense_application_agent_tool
        ctx = self._make_context(application_date="bad-date")
        result = expense_application_agent_tool(query="経費申請", tool_context=ctx)
        assert "エラー" in result

    def test_valid_call_returns_string(self):
        from agents.expense_agent import expense_application_agent_tool

        mock_agent = MagicMock(return_value="経費申請完了")
        with patch("agents.expense_agent.ExpenseAgentFactory.get_agent", return_value=mock_agent):
            ctx = self._make_context()
            result = expense_application_agent_tool(query="経費申請テスト", tool_context=ctx)

        assert isinstance(result, str)

    def test_loop_limit_error_returns_message(self):
        from agents.expense_agent import expense_application_agent_tool
        from handlers.exceptions import LoopLimitError

        mock_agent = MagicMock(side_effect=LoopLimitError(30, 30, "expense_agent"))
        with patch("agents.expense_agent.ExpenseAgentFactory.get_agent", return_value=mock_agent):
            ctx = self._make_context()
            result = expense_application_agent_tool(query="テスト", tool_context=ctx)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_unexpected_error_returns_message(self):
        from agents.expense_agent import expense_application_agent_tool

        mock_agent = MagicMock(side_effect=Exception("unexpected"))
        with patch("agents.expense_agent.ExpenseAgentFactory.get_agent", return_value=mock_agent):
            ctx = self._make_context()
            result = expense_application_agent_tool(query="テスト", tool_context=ctx)

        assert isinstance(result, str)


class TestBuildExpenseAgentSystemPrompt:
    def test_contains_application_date(self):
        from agents.expense_agent import _build_expense_agent_system_prompt
        result = _build_expense_agent_system_prompt("2026-04-28", 3, 5000, ["事務用品費", "宿泊費"])
        assert "2026-04-28" in result

    def test_contains_deadline_date(self):
        from agents.expense_agent import _build_expense_agent_system_prompt
        result = _build_expense_agent_system_prompt("2026-04-28", 3, 5000, ["事務用品費"])
        assert "2026-01-28" in result

    def test_contains_manager_threshold(self):
        from agents.expense_agent import _build_expense_agent_system_prompt
        result = _build_expense_agent_system_prompt("2026-04-28", 3, 5000, ["事務用品費"])
        assert "5000" in result

    def test_contains_expense_categories(self):
        from agents.expense_agent import _build_expense_agent_system_prompt
        result = _build_expense_agent_system_prompt(
            "2026-04-28", 3, 5000, ["事務用品費", "宿泊費", "資格精算費", "その他経費"]
        )
        assert "事務用品費" in result
        assert "宿泊費" in result

    def test_invalid_date_does_not_raise(self):
        from agents.expense_agent import _build_expense_agent_system_prompt
        result = _build_expense_agent_system_prompt("invalid", 3, 5000, ["事務用品費"])
        assert isinstance(result, str)
