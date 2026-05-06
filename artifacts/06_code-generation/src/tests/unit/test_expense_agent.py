# 参照: DD-02c 経費精算申請エージェント詳細設計書
"""agents/expense_agent.py の単体テスト"""
import sys
import os
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def make_tool_context(session_id="sess_expense_test", applicant_name="山田太郎", application_date="2026-05-06"):
    ctx = MagicMock()
    ctx.invocation_state = {
        "session_id": session_id,
        "applicant_name": applicant_name,
        "application_date": application_date,
    }
    return ctx


class TestExpenseAgentTool:
    """expense_agent_tool の単体テスト"""

    def setup_method(self):
        """各テスト前にキャッシュをクリアする。"""
        import agents.expense_agent as ea
        ea._agent_instances.clear()

    def test_loop_limit_error_returns_str(self):
        """LoopLimitError発生時WARNINGログ出力後エラーメッセージstrが返ること（モック使用）。"""
        from handlers.error_handler import LoopLimitError
        import agents.expense_agent as ea

        ea._STRANDS_AVAILABLE = True
        mock_agent = MagicMock()
        mock_agent.side_effect = LoopLimitError(10, 10, "expense_agent")
        ea._agent_instances["test_loop_expense"] = mock_agent

        from agents.expense_agent import expense_agent_tool
        ctx = make_tool_context(session_id="test_loop_expense")
        result = expense_agent_tool("テストクエリ", tool_context=ctx)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_agent_instance_cached(self):
        """同じsession_idで呼び出した場合、Agentインスタンスが再利用されること。"""
        import agents.expense_agent as ea

        mock_agent = MagicMock()
        mock_agent.return_value = "応答テキスト"
        ea._STRANDS_AVAILABLE = True
        ea._agent_instances["cached_expense"] = mock_agent

        from agents.expense_agent import expense_agent_tool
        ctx = make_tool_context(session_id="cached_expense")

        expense_agent_tool("クエリ1", tool_context=ctx)
        expense_agent_tool("クエリ2", tool_context=ctx)

        assert mock_agent.call_count == 2

    def test_invocation_state_excludes_session_id(self):
        """子エージェントへ渡すinvocation_stateにsession_idが含まれないこと。"""
        import agents.expense_agent as ea

        captured_state = {}

        def mock_call(query, invocation_state=None):
            if invocation_state:
                captured_state.update(invocation_state)
            return "応答"

        mock_agent = MagicMock()
        mock_agent.side_effect = mock_call
        ea._STRANDS_AVAILABLE = True
        ea._agent_instances["test_state_expense"] = mock_agent

        from agents.expense_agent import expense_agent_tool
        ctx = make_tool_context(session_id="test_state_expense")
        expense_agent_tool("クエリ", tool_context=ctx)

        assert "session_id" not in captured_state
        assert "applicant_name" in captured_state

    def test_tools_list_excludes_calculate_transport_fare(self):
        """expense_agent_toolがtoolsリストにcalculate_transport_fareを含まないこと。

        注: このテストはAgentインスタンス生成時の構成を検証するため、
        strands未インストール環境では新規生成をスキップする。
        """
        import agents.expense_agent as ea

        if not ea._STRANDS_AVAILABLE:
            pytest.skip("strands-agents not available")

        # モックを使ってAgent生成時のtools引数を検証する
        agent_calls = []

        class MockAgent:
            def __init__(self, **kwargs):
                agent_calls.append(kwargs)
                self.invocation_state = {}
            def __call__(self, query, **kwargs):
                return "応答"

        with patch("agents.expense_agent.Agent", MockAgent):
            with patch("agents.expense_agent._STRANDS_AVAILABLE", True):
                # 依存モジュールをモック
                mock_modules = {
                    "config.model_config": MagicMock(),
                    "prompt.prompt_expense": MagicMock(get_expense_system_prompt=MagicMock(return_value="prompt")),
                    "tools.output_generator": MagicMock(generate_expense_application=MagicMock()),
                    "session.session_manager": MagicMock(),
                    "strands_tools": MagicMock(image_reader=MagicMock()),
                }
                for mod_name, mock_mod in mock_modules.items():
                    if mod_name in sys.modules:
                        del sys.modules[mod_name]

                ea._agent_instances.clear()
                # ToolContextのモックでAgent生成を誘発
                ctx = make_tool_context(session_id="new_expense_session")
                from agents.expense_agent import expense_agent_tool

                with patch.dict(sys.modules, mock_modules):
                    result = expense_agent_tool("クエリ", tool_context=ctx)

        # calculate_transport_fareがtoolsに含まれていないことを検証（DDから確認）
        if agent_calls:
            tools_arg = agent_calls[0].get("tools", [])
            tool_names = [getattr(t, "__name__", str(t)) for t in tools_arg]
            assert "calculate_transport_fare" not in tool_names, \
                f"calculate_transport_fare should not be in expense agent tools: {tool_names}"
