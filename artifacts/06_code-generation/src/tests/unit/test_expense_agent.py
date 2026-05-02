import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unittest.mock import MagicMock, patch


def make_context(session_id="sess1", applicant_name="田中太郎", application_date="2026-05-02"):
    ctx = MagicMock()
    ctx.invocation_state = {
        "session_id": session_id,
        "applicant_name": applicant_name,
        "application_date": application_date,
    }
    return ctx


class TestExpenseAgentTool:
    def setup_method(self):
        import agents.expense_agent as mod
        mod._agent_instances.clear()

    def test_import_ok(self):
        from agents.expense_agent import expense_agent_tool
        assert callable(expense_agent_tool)

    def test_creates_new_instance_for_new_session(self):
        import agents.expense_agent as mod
        mock_agent = MagicMock(return_value="response")
        with patch.object(mod, "_build_expense_agent", return_value=mock_agent):
            result = mod.expense_agent_tool.__wrapped__(
                make_context("new_sess"),
                "経費精算申請",
                "田中太郎",
                "事務用品を購入",
            )
        assert "new_sess" in mod._agent_instances
        assert result == "response"

    def test_reuses_cached_instance(self):
        import agents.expense_agent as mod
        mock_agent = MagicMock(return_value="response")
        mod._agent_instances["sess1"] = mock_agent
        with patch.object(mod, "_build_expense_agent") as build_mock:
            mod.expense_agent_tool.__wrapped__(
                make_context("sess1"),
                "経費精算申請",
                "田中太郎",
                "text",
            )
        build_mock.assert_not_called()

    def test_returns_string(self):
        import agents.expense_agent as mod
        mock_agent = MagicMock(return_value="申請書生成完了")
        with patch.object(mod, "_build_expense_agent", return_value=mock_agent):
            result = mod.expense_agent_tool.__wrapped__(
                make_context(), "経費精算申請", "田中太郎", "ボールペン購入"
            )
        assert isinstance(result, str)
        assert "申請書生成完了" in result

    def test_loop_limit_error_handled(self):
        import agents.expense_agent as mod
        from handlers.loop_control_hook import LoopLimitError
        mock_agent = MagicMock(side_effect=LoopLimitError(current_iteration=10, max_iterations=10, agent_name="AG-003"))
        with patch.object(mod, "_build_expense_agent", return_value=mock_agent):
            result = mod.expense_agent_tool.__wrapped__(
                make_context(), "経費精算申請", "田中太郎", "text"
            )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_unexpected_error_handled(self):
        import agents.expense_agent as mod
        mock_agent = MagicMock(side_effect=Exception("unexpected"))
        with patch.object(mod, "_build_expense_agent", return_value=mock_agent):
            result = mod.expense_agent_tool.__wrapped__(
                make_context(), "経費精算申請", "田中太郎", "text"
            )
        assert isinstance(result, str)
