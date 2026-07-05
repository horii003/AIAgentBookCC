"""transport_application_agentの単体テスト"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from unittest.mock import MagicMock, patch


class TestBuildTransportApplicationAgent:
    def test_Agentインスタンスを返す(self):
        mock_agent = MagicMock()
        with patch("agents.transport_application_agent.create_specialist_agent", return_value=mock_agent) as mock_create:
            from agents.transport_application_agent import _build_transport_application_agent
            result = _build_transport_application_agent(
                session_id="20260703120000_abc12345",
                applicant_name="山田太郎",
                application_date="2026-07-03",
                deadline="2026-10-03",
            )
        assert result is mock_agent
        mock_create.assert_called_once()

    def test_create_specialist_agentにtoolsが渡される(self):
        mock_agent = MagicMock()
        with patch("agents.transport_application_agent.create_specialist_agent", return_value=mock_agent) as mock_create:
            from agents.transport_application_agent import _build_transport_application_agent
            _build_transport_application_agent(
                session_id="20260703120000_abc12345",
                applicant_name="山田太郎",
                application_date="2026-07-03",
                deadline="2026-10-03",
            )
        call_kwargs = mock_create.call_args[1]
        assert len(call_kwargs["tools"]) == 2

    def test_create_specialist_agentにagent_nameが渡される(self):
        mock_agent = MagicMock()
        with patch("agents.transport_application_agent.create_specialist_agent", return_value=mock_agent) as mock_create:
            from agents.transport_application_agent import _build_transport_application_agent
            _build_transport_application_agent(
                session_id="20260703120000_abc12345",
                applicant_name="山田太郎",
                application_date="2026-07-03",
                deadline="2026-10-03",
            )
        call_kwargs = mock_create.call_args[1]
        assert "交通費" in call_kwargs["agent_name"]


class TestTransportApplicationAgent:
    def test_invoke_specialist_agentを呼び出す(self):
        ctx = MagicMock()
        ctx.invocation_state = {
            "applicant_name": "山田太郎",
            "application_date": "2026-07-03",
            "session_id": "sess_abc12345",
        }

        with patch("agents.transport_application_agent.invoke_specialist_agent", return_value="応答") as mock_invoke:
            from agents.transport_application_agent import transport_application_agent
            result = transport_application_agent(query="交通費申請", tool_context=ctx)

        mock_invoke.assert_called_once()
        call_kwargs = mock_invoke.call_args[1]
        assert call_kwargs["agent_id"] == "AG-002"
        assert result == "応答"
