"""base_agentの単体テスト"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from unittest.mock import MagicMock, patch
from agents.base_agent import calculate_deadline, invoke_specialist_agent
from handlers.error_handler import LoopLimitError


class TestCalculateDeadline:
    def test_3ヶ月後の期限を計算する(self):
        result = calculate_deadline("2026-01-15", 3)
        assert result == "2026-04-15"

    def test_月末の繰り越しが正しく処理される(self):
        result = calculate_deadline("2026-01-31", 1)
        assert result == "2026-02-28"

    def test_12ヶ月後は翌年になる(self):
        result = calculate_deadline("2026-01-01", 12)
        assert result == "2027-01-01"

    def test_不正な日付文字列で要確認を返す(self):
        result = calculate_deadline("not-a-date", 3)
        assert result == "要確認"

    def test_空文字で要確認を返す(self):
        result = calculate_deadline("", 3)
        assert result == "要確認"


class TestInvokeSpecialistAgent:
    def _make_context(self, applicant="山田太郎", application_date="2026-07-03", session_id="sess_abc12345"):
        ctx = MagicMock()
        ctx.invocation_state = {
            "applicant_name": applicant,
            "application_date": application_date,
            "session_id": session_id,
        }
        return ctx

    def test_正常系でエージェントの応答を返す(self):
        ctx = self._make_context()
        mock_agent = MagicMock()
        mock_agent.return_value = "処理が完了しました。"
        build_agent = MagicMock(return_value=mock_agent)

        result = invoke_specialist_agent(
            query="交通費精算申請をしたい",
            tool_context=ctx,
            agent_id="AG-002",
            deadline_months=3,
            build_agent=build_agent,
        )

        assert "処理が完了しました" in result
        build_agent.assert_called_once()

    def test_LoopLimitErrorがハンドリングされる(self):
        ctx = self._make_context()
        mock_agent = MagicMock()
        mock_agent.side_effect = LoopLimitError(
            current_iteration=11, max_iterations=10, agent_name="AG-002"
        )
        build_agent = MagicMock(return_value=mock_agent)

        result = invoke_specialist_agent(
            query="申請",
            tool_context=ctx,
            agent_id="AG-002",
            deadline_months=3,
            build_agent=build_agent,
        )

        assert isinstance(result, str)
        assert len(result) > 0

    def test_予期しない例外がハンドリングされる(self):
        ctx = self._make_context()
        mock_agent = MagicMock()
        mock_agent.side_effect = RuntimeError("unexpected")
        build_agent = MagicMock(return_value=mock_agent)

        result = invoke_specialist_agent(
            query="申請",
            tool_context=ctx,
            agent_id="AG-002",
            deadline_months=3,
            build_agent=build_agent,
        )

        assert isinstance(result, str)
        assert len(result) > 0

    def test_invocation_stateが子エージェントに渡される(self):
        ctx = self._make_context()
        mock_agent = MagicMock()
        mock_agent.return_value = "OK"
        build_agent = MagicMock(return_value=mock_agent)

        invoke_specialist_agent(
            query="申請",
            tool_context=ctx,
            agent_id="AG-002",
            deadline_months=3,
            build_agent=build_agent,
        )

        call_kwargs = mock_agent.call_args
        invocation_state = call_kwargs.kwargs.get("invocation_state") or call_kwargs[1].get("invocation_state")
        assert invocation_state["applicant_name"] == "山田太郎"
        assert invocation_state["application_date"] == "2026-07-03"
        assert "session_id" not in invocation_state
