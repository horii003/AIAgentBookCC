"""expense_agent.py の単体テスト"""
import pytest
from unittest.mock import patch, MagicMock

from agents.expense_agent import handle_expense_application, _agent_instances


def _make_tool_context(session_id="test-session-001", applicant_name="山田太郎", application_date="2026-05-01"):
    from strands.types.tools import ToolContext
    ctx = MagicMock(spec=ToolContext)
    ctx.invocation_state = {
        "session_id": session_id,
        "applicant_name": applicant_name,
        "application_date": application_date,
    }
    return ctx


class TestHandleExpenseApplication:
    def setup_method(self):
        """テスト前にキャッシュをクリアする"""
        _agent_instances.clear()

    def test_new_session_creates_agent_instance(self):
        """新規 session_id で Agent インスタンスが生成されること"""
        ctx = _make_tool_context(session_id="expense-new-001")
        mock_agent = MagicMock(return_value="経費申請完了")

        with patch("agents.expense_agent.Agent", return_value=mock_agent), \
             patch("agents.expense_agent.SessionManagerFactory.create"), \
             patch("agents.expense_agent.ModelConfig.get_model"):
            result = handle_expense_application("経費申請お願いします", ctx)

        assert "expense-new-001" in _agent_instances

    def test_same_session_reuses_agent_instance(self):
        """同一 session_id で Agent インスタンスが再利用されること"""
        ctx = _make_tool_context(session_id="expense-reuse-001")
        mock_agent = MagicMock(return_value="応答")

        with patch("agents.expense_agent.Agent", return_value=mock_agent) as mock_agent_cls, \
             patch("agents.expense_agent.SessionManagerFactory.create"), \
             patch("agents.expense_agent.ModelConfig.get_model"):
            handle_expense_application("クエリ1", ctx)
            handle_expense_application("クエリ2", ctx)

        assert mock_agent_cls.call_count == 1

    def test_session_id_not_in_inner_state(self):
        """子エージェントへの invocation_state に session_id が含まれること（AG-001 からは渡す）"""
        ctx = _make_tool_context(session_id="expense-state-session")
        captured_kwargs = {}
        mock_agent_instance = MagicMock(return_value="応答")

        def mock_call(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return "応答"

        mock_agent_instance.side_effect = mock_call

        with patch("agents.expense_agent.Agent", return_value=mock_agent_instance), \
             patch("agents.expense_agent.SessionManagerFactory.create"), \
             patch("agents.expense_agent.ModelConfig.get_model"):
            handle_expense_application("テスト", ctx)

        state = captured_kwargs.get("invocation_state", {})
        assert state.get("applicant_name") == "山田太郎"

    def test_loop_limit_error_returns_str(self):
        """LoopLimitError 発生時に str 型のエラーメッセージが返されること"""
        from handlers.loop_control_hook import LoopLimitError
        ctx = _make_tool_context(session_id="expense-loop-error")
        mock_agent = MagicMock(
            side_effect=LoopLimitError(
                current_iteration=30,
                max_iterations=30,
                agent_name="expense_agent",
            )
        )

        with patch("agents.expense_agent.Agent", return_value=mock_agent), \
             patch("agents.expense_agent.SessionManagerFactory.create"), \
             patch("agents.expense_agent.ModelConfig.get_model"):
            result = handle_expense_application("クエリ", ctx)

        assert isinstance(result, str)

    def test_runtime_error_returns_str(self):
        """RuntimeError 発生時に str 型のエラーメッセージが返されること"""
        ctx = _make_tool_context(session_id="expense-runtime-error")
        mock_agent = MagicMock(side_effect=RuntimeError("テストエラー"))

        with patch("agents.expense_agent.Agent", return_value=mock_agent), \
             patch("agents.expense_agent.SessionManagerFactory.create"), \
             patch("agents.expense_agent.ModelConfig.get_model"):
            result = handle_expense_application("クエリ", ctx)

        assert isinstance(result, str)

    def test_callback_handler_is_none(self):
        """callback_handler=None が設定されること"""
        ctx = _make_tool_context(session_id="expense-callback-none")
        captured_kwargs = {}

        def mock_agent_constructor(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return MagicMock(return_value="応答")

        with patch("agents.expense_agent.Agent", side_effect=mock_agent_constructor), \
             patch("agents.expense_agent.SessionManagerFactory.create"), \
             patch("agents.expense_agent.ModelConfig.get_model"):
            handle_expense_application("クエリ", ctx)

        assert captured_kwargs.get("callback_handler") is None

    def test_unexpected_error_returns_str(self):
        """想定外 Exception 発生時に str 型のエラーメッセージが返されること"""
        ctx = _make_tool_context(session_id="expense-unexpected-error")
        mock_agent = MagicMock(side_effect=Exception("想定外エラー"))

        with patch("agents.expense_agent.Agent", return_value=mock_agent), \
             patch("agents.expense_agent.SessionManagerFactory.create"), \
             patch("agents.expense_agent.ModelConfig.get_model"):
            result = handle_expense_application("クエリ", ctx)

        assert isinstance(result, str)
