import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unittest.mock import MagicMock, patch


class TestOrchestratorAgentModule:
    def test_import_ok(self):
        from agents.orchestrator_agent import create_orchestrator_agent
        assert callable(create_orchestrator_agent)

    def test_create_agent_returns_agent(self):
        with patch("agents.orchestrator_agent.BedrockModel"):
            from agents.orchestrator_agent import create_orchestrator_agent
            from strands import Agent
            agent = create_orchestrator_agent()
            assert isinstance(agent, Agent)

    def test_transport_tool_registered(self):
        with patch("agents.orchestrator_agent.BedrockModel"):
            from agents.orchestrator_agent import create_orchestrator_agent
            agent = create_orchestrator_agent()
            assert "transport_agent_tool" in agent.tool_names

    def test_expense_tool_registered(self):
        with patch("agents.orchestrator_agent.BedrockModel"):
            from agents.orchestrator_agent import create_orchestrator_agent
            agent = create_orchestrator_agent()
            assert "expense_agent_tool" in agent.tool_names
