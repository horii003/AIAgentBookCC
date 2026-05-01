"""transport_agent.py の単体テスト"""
import pytest
from unittest.mock import patch, MagicMock

from agents.transport_agent import handle_transport_expense_application, _agent_instances


def _make_tool_context(session_id="test-session-001", applicant_name="山田太郎", application_date="2026-05-01"):
    from strands.types.tools import ToolContext
    ctx = MagicMock(spec=ToolContext)
    ctx.invocation_state = {
        "session_id": session_id,
        "applicant_name": applicant_name,
        "application_date": application_date,
    }
    return ctx


class TestHandleTransportExpenseApplication:
    def setup_method(self):
        """テスト前にキャッシュをクリアする"""
        _agent_instances.clear()

    def test_new_session_creates_agent_instance(self):
        """新規 session_id で Agent インスタンスが生成されること"""
        ctx = _make_tool_context(session_id="new-session-001")
        mock_agent = MagicMock(return_value="交通費申請完了")

        with patch("agents.transport_agent.Agent", return_value=mock_agent), \
             patch("agents.transport_agent.SessionManagerFactory.create"), \
             patch("agents.transport_agent.ModelConfig.get_model"):
            result = handle_transport_expense_application("交通費申請お願いします", ctx)

        assert "new-session-001" in _agent_instances

    def test_same_session_reuses_agent_instance(self):
        """同一 session_id で Agent インスタンスが再利用されること"""
        ctx = _make_tool_context(session_id="reuse-session-001")
        mock_agent = MagicMock(return_value="応答")

        with patch("agents.transport_agent.Agent", return_value=mock_agent) as mock_agent_cls, \
             patch("agents.transport_agent.SessionManagerFactory.create"), \
             patch("agents.transport_agent.ModelConfig.get_model"):
            handle_transport_expense_application("クエリ1", ctx)
            handle_transport_expense_application("クエリ2", ctx)

        assert mock_agent_cls.call_count == 1

    def test_different_sessions_create_different_instances(self):
        """異なる session_id で異なるインスタンスが生成されること"""
        ctx1 = _make_tool_context(session_id="session-A")
        ctx2 = _make_tool_context(session_id="session-B")
        mock_agent = MagicMock(return_value="応答")

        with patch("agents.transport_agent.Agent", return_value=mock_agent), \
             patch("agents.transport_agent.SessionManagerFactory.create"), \
             patch("agents.transport_agent.ModelConfig.get_model"):
            handle_transport_expense_application("クエリ1", ctx1)
            handle_transport_expense_application("クエリ2", ctx2)

        assert "session-A" in _agent_instances
        assert "session-B" in _agent_instances

    def test_invocation_state_passed_to_agent(self):
        """invocation_state がエージェント呼び出し時に渡されること"""
        ctx = _make_tool_context(session_id="state-test-session")
        captured_kwargs = {}
        mock_agent_instance = MagicMock(return_value="応答")

        def mock_call(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return "応答"

        mock_agent_instance.side_effect = mock_call

        with patch("agents.transport_agent.Agent", return_value=mock_agent_instance), \
             patch("agents.transport_agent.SessionManagerFactory.create"), \
             patch("agents.transport_agent.ModelConfig.get_model"):
            handle_transport_expense_application("テスト", ctx)

        assert "invocation_state" in captured_kwargs
        state = captured_kwargs["invocation_state"]
        assert state.get("applicant_name") == "山田太郎"
        assert "session_id" in state

    def test_loop_limit_error_returns_str(self):
        """LoopLimitError 発生時に str 型のエラーメッセージが返されること"""
        from handlers.loop_control_hook import LoopLimitError
        ctx = _make_tool_context(session_id="loop-error-session")
        mock_agent = MagicMock(
            side_effect=LoopLimitError(
                current_iteration=30,
                max_iterations=30,
                agent_name="transport_agent",
            )
        )

        with patch("agents.transport_agent.Agent", return_value=mock_agent), \
             patch("agents.transport_agent.SessionManagerFactory.create"), \
             patch("agents.transport_agent.ModelConfig.get_model"):
            result = handle_transport_expense_application("クエリ", ctx)

        assert isinstance(result, str)

    def test_runtime_error_returns_str(self):
        """RuntimeError 発生時に str 型のエラーメッセージが返されること"""
        ctx = _make_tool_context(session_id="runtime-error-session")
        mock_agent = MagicMock(side_effect=RuntimeError("テストエラー"))

        with patch("agents.transport_agent.Agent", return_value=mock_agent), \
             patch("agents.transport_agent.SessionManagerFactory.create"), \
             patch("agents.transport_agent.ModelConfig.get_model"):
            result = handle_transport_expense_application("クエリ", ctx)

        assert isinstance(result, str)

    def test_callback_handler_is_none(self):
        """callback_handler=None が設定されること"""
        ctx = _make_tool_context(session_id="callback-none-session")
        captured_kwargs = {}

        def mock_agent_constructor(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return MagicMock(return_value="応答")

        with patch("agents.transport_agent.Agent", side_effect=mock_agent_constructor), \
             patch("agents.transport_agent.SessionManagerFactory.create"), \
             patch("agents.transport_agent.ModelConfig.get_model"):
            handle_transport_expense_application("クエリ", ctx)

        assert captured_kwargs.get("callback_handler") is None
