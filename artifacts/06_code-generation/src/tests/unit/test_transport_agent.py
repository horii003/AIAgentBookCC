# 参照: DD-02b 交通費精算申請エージェント詳細設計書
"""agents/transport_agent.py の単体テスト"""
import sys
import os
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def make_tool_context(session_id="sess_test", applicant_name="山田太郎", application_date="2026-05-06"):
    ctx = MagicMock()
    ctx.invocation_state = {
        "session_id": session_id,
        "applicant_name": applicant_name,
        "application_date": application_date,
    }
    return ctx


class TestTransportAgentTool:
    """transport_agent_tool の単体テスト"""

    def setup_method(self):
        """各テスト前にキャッシュをクリアする。"""
        import agents.transport_agent as ta
        ta._agent_instances.clear()

    def test_loop_limit_error_returns_str(self):
        """LoopLimitError発生時WARNINGログ出力後エラーメッセージstrが返ること（モック使用）。"""
        from handlers.error_handler import LoopLimitError
        import agents.transport_agent as ta

        ta._STRANDS_AVAILABLE = True
        mock_agent = MagicMock()
        mock_agent.side_effect = LoopLimitError(10, 10, "transport_agent")

        ta._agent_instances["test_loop"] = mock_agent

        # transport_agent_toolを直接呼び出す（モック差し込み）
        from agents.transport_agent import transport_agent_tool
        ctx = make_tool_context(session_id="test_loop")
        result = transport_agent_tool("テストクエリ", tool_context=ctx)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_exception_returns_str(self):
        """Exception発生時ERRORログ（exc_info=True）出力後エラーメッセージstrが返ること。"""
        import agents.transport_agent as ta

        ta._STRANDS_AVAILABLE = True
        mock_agent = MagicMock()
        mock_agent.side_effect = Exception("test error")

        ta._agent_instances["test_exc"] = mock_agent

        from agents.transport_agent import transport_agent_tool
        ctx = make_tool_context(session_id="test_exc")
        result = transport_agent_tool("テストクエリ", tool_context=ctx)
        assert isinstance(result, str)

    def test_agent_instance_cached(self):
        """同じsession_idで呼び出した場合、Agentインスタンスが再利用されること。"""
        import agents.transport_agent as ta

        # 既存のインスタンスをモックとして事前登録
        mock_agent = MagicMock()
        mock_agent.return_value = "応答テキスト"
        ta._STRANDS_AVAILABLE = True
        ta._agent_instances["cached_session"] = mock_agent

        from agents.transport_agent import transport_agent_tool
        ctx = make_tool_context(session_id="cached_session")

        # 1回目
        transport_agent_tool("クエリ1", tool_context=ctx)
        # 2回目（同一session_id）
        transport_agent_tool("クエリ2", tool_context=ctx)

        # インスタンスが再利用されていること（同じモックが2回呼ばれること）
        assert mock_agent.call_count == 2

    def test_invocation_state_excludes_session_id(self):
        """子エージェントへ渡すinvocation_stateにsession_idが含まれないこと。"""
        import agents.transport_agent as ta

        captured_invocation_state = {}

        def mock_agent_call(query, invocation_state=None):
            if invocation_state:
                captured_invocation_state.update(invocation_state)
            return "応答"

        mock_agent = MagicMock()
        mock_agent.side_effect = mock_agent_call
        ta._STRANDS_AVAILABLE = True
        ta._agent_instances["test_state"] = mock_agent

        from agents.transport_agent import transport_agent_tool
        ctx = make_tool_context(session_id="test_state")
        transport_agent_tool("クエリ", tool_context=ctx)

        # session_idが含まれないこと（マルチエージェント連携設計 7.3準拠）
        assert "session_id" not in captured_invocation_state
        # applicant_name・application_dateは含まれること
        assert "applicant_name" in captured_invocation_state
        assert "application_date" in captured_invocation_state
