"""結合テスト: エージェント-ツール連携の検証"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from unittest.mock import MagicMock, patch


class TestOrchestratorToolWiring:
    """AG-001 が AG-002/AG-003 ツールを正しく保持しているか検証する。"""

    def test_orchestrator_has_transport_tool(self):
        with patch("agents.orchestrator_agent.BedrockModel"):
            from agents.orchestrator_agent import create_orchestrator_agent
            agent = create_orchestrator_agent()
        assert "transport_agent_tool" in agent.tool_names

    def test_orchestrator_has_expense_tool(self):
        with patch("agents.orchestrator_agent.BedrockModel"):
            from agents.orchestrator_agent import create_orchestrator_agent
            agent = create_orchestrator_agent()
        assert "expense_agent_tool" in agent.tool_names

    def test_orchestrator_has_exactly_two_tools(self):
        with patch("agents.orchestrator_agent.BedrockModel"):
            from agents.orchestrator_agent import create_orchestrator_agent
            agent = create_orchestrator_agent()
        assert len(agent.tool_names) == 2


class TestTransportAgentToolWiring:
    """AG-002 が calculate_transport_fare / generate_transport_expense_form を保持しているか検証する。"""

    def test_transport_agent_has_fare_tool(self):
        with patch("agents.transport_agent.BedrockModel"):
            from agents.transport_agent import _build_transport_agent
            agent = _build_transport_agent("2026-05-02")
        assert "calculate_transport_fare" in agent.tool_names

    def test_transport_agent_has_form_tool(self):
        with patch("agents.transport_agent.BedrockModel"):
            from agents.transport_agent import _build_transport_agent
            agent = _build_transport_agent("2026-05-02")
        assert "generate_transport_expense_form" in agent.tool_names


class TestExpenseAgentToolWiring:
    """AG-003 が image_reader / generate_expense_reimbursement_form を保持しているか検証する。"""

    def test_expense_agent_has_image_reader(self):
        with patch("agents.expense_agent.BedrockModel"):
            from agents.expense_agent import _build_expense_agent
            agent = _build_expense_agent("2026-05-02")
        assert "image_reader" in agent.tool_names

    def test_expense_agent_has_form_tool(self):
        with patch("agents.expense_agent.BedrockModel"):
            from agents.expense_agent import _build_expense_agent
            agent = _build_expense_agent("2026-05-02")
        assert "generate_expense_reimbursement_form" in agent.tool_names


class TestSessionIdPropagation:
    """session_id が invocation_state 経由で正しく伝播するか検証する。"""

    def setup_method(self):
        import agents.transport_agent as mod
        mod._agent_instances.clear()
        import agents.expense_agent as mod2
        mod2._agent_instances.clear()

    def test_transport_agent_caches_by_session_id(self):
        import agents.transport_agent as mod
        mock_agent = MagicMock(return_value="ok")
        with patch.object(mod, "_build_transport_agent", return_value=mock_agent):
            ctx1 = MagicMock()
            ctx1.invocation_state = {"session_id": "s1", "applicant_name": "田中", "application_date": "2026-05-02"}
            ctx2 = MagicMock()
            ctx2.invocation_state = {"session_id": "s2", "applicant_name": "鈴木", "application_date": "2026-05-02"}
            mod.transport_agent_tool.__wrapped__(ctx1, "交通費精算申請", "田中", "text")
            mod.transport_agent_tool.__wrapped__(ctx2, "交通費精算申請", "鈴木", "text")
        assert "s1" in mod._agent_instances
        assert "s2" in mod._agent_instances
        assert mod._agent_instances["s1"] is mod._agent_instances["s2"]

    def test_expense_agent_caches_by_session_id(self):
        import agents.expense_agent as mod
        mock_agent = MagicMock(return_value="ok")
        with patch.object(mod, "_build_expense_agent", return_value=mock_agent):
            ctx = MagicMock()
            ctx.invocation_state = {"session_id": "sx", "applicant_name": "田中", "application_date": "2026-05-02"}
            mod.expense_agent_tool.__wrapped__(ctx, "経費精算申請", "田中", "text")
            mod.expense_agent_tool.__wrapped__(ctx, "経費精算申請", "田中", "second call")
        assert "sx" in mod._agent_instances
        assert mock_agent.call_count == 2
