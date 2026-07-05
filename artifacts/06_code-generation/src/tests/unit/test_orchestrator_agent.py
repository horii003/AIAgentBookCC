"""orchestrator_agentの単体テスト"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from unittest.mock import MagicMock, patch
from agents.orchestrator_agent import OrchestratorAgent


def _make_agent(mock_agent_response="OK"):
    oa = OrchestratorAgent()
    mock_transport = MagicMock()
    mock_expense = MagicMock()
    mock_agent = MagicMock()
    mock_agent.return_value = mock_agent_response

    with patch("agents.orchestrator_agent.Agent", return_value=mock_agent):
        with patch("agents.orchestrator_agent.SessionManagerFactory"):
            with patch("agents.orchestrator_agent.ModelConfig"):
                oa._initialize(mock_transport, mock_expense)

    oa.agent = mock_agent
    oa._session_id = "20260703120000_abc12345"
    return oa, mock_agent


class TestOrchestratorAgentInitialize:
    def test_session_idが生成される(self):
        oa = OrchestratorAgent()
        mock_transport = MagicMock()
        mock_expense = MagicMock()

        with patch("agents.orchestrator_agent.Agent") as mock_agent_cls:
            with patch("agents.orchestrator_agent.SessionManagerFactory") as mock_factory:
                mock_factory.generate_session_id.return_value = "20260703120000_testid"
                with patch("agents.orchestrator_agent.ModelConfig"):
                    oa._initialize(mock_transport, mock_expense)

        assert oa._session_id == "20260703120000_testid"

    def test_agentインスタンスが生成される(self):
        oa = OrchestratorAgent()
        mock_transport = MagicMock()
        mock_expense = MagicMock()

        with patch("agents.orchestrator_agent.Agent") as mock_agent_cls:
            mock_agent_cls.return_value = MagicMock()
            with patch("agents.orchestrator_agent.SessionManagerFactory"):
                with patch("agents.orchestrator_agent.ModelConfig"):
                    oa._initialize(mock_transport, mock_expense)

        assert oa.agent is not None


class TestOrchestratorAgentRun:
    def test_quitで終了する(self):
        oa, mock_agent = _make_agent()

        with patch("builtins.input", side_effect=["quit"]):
            with patch("builtins.print"):
                with patch("agents.orchestrator_agent.Agent", return_value=mock_agent):
                    with patch("agents.orchestrator_agent.SessionManagerFactory"):
                        with patch("agents.orchestrator_agent.ModelConfig"):
                            oa.run(MagicMock(), MagicMock())

        mock_agent.assert_not_called()

    def test_exitで終了する(self):
        oa, mock_agent = _make_agent()

        with patch("builtins.input", side_effect=["exit"]):
            with patch("builtins.print"):
                with patch("agents.orchestrator_agent.Agent", return_value=mock_agent):
                    with patch("agents.orchestrator_agent.SessionManagerFactory"):
                        with patch("agents.orchestrator_agent.ModelConfig"):
                            oa.run(MagicMock(), MagicMock())

        mock_agent.assert_not_called()

    def test_ユーザー入力がエージェントに渡される(self):
        oa, mock_agent = _make_agent()

        with patch("builtins.input", side_effect=["交通費精算申請をしたい", "quit"]):
            with patch("builtins.print"):
                with patch("agents.orchestrator_agent.Agent", return_value=mock_agent):
                    with patch("agents.orchestrator_agent.SessionManagerFactory"):
                        with patch("agents.orchestrator_agent.ModelConfig"):
                            oa.run(MagicMock(), MagicMock())

        mock_agent.assert_called_once()
        call_args = mock_agent.call_args
        assert call_args[0][0] == "交通費精算申請をしたい"

    def test_invocation_stateにapplication_dateが含まれる(self):
        oa, mock_agent = _make_agent()

        with patch("builtins.input", side_effect=["申請したい", "quit"]):
            with patch("builtins.print"):
                with patch("agents.orchestrator_agent.Agent", return_value=mock_agent):
                    with patch("agents.orchestrator_agent.SessionManagerFactory"):
                        with patch("agents.orchestrator_agent.ModelConfig"):
                            oa.run(MagicMock(), MagicMock())

        call_kwargs = mock_agent.call_args[1]
        assert "application_date" in call_kwargs["invocation_state"]

    def test_EOFErrorで正常終了する(self):
        oa, mock_agent = _make_agent()

        with patch("builtins.input", side_effect=EOFError()):
            with patch("builtins.print"):
                with patch("agents.orchestrator_agent.Agent", return_value=mock_agent):
                    with patch("agents.orchestrator_agent.SessionManagerFactory"):
                        with patch("agents.orchestrator_agent.ModelConfig"):
                            oa.run(MagicMock(), MagicMock())
