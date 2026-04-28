"""prompt_orchestrator.py の単体テスト"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from prompt.prompt_orchestrator import ORCHESTRATOR_SYSTEM_PROMPT


class TestOrchestratorSystemPrompt:
    def test_非空文字列である(self):
        assert isinstance(ORCHESTRATOR_SYSTEM_PROMPT, str)
        assert len(ORCHESTRATOR_SYSTEM_PROMPT) > 0

    def test_travel_application_agent_tool_が含まれる(self):
        assert "travel_application_agent_tool" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_expense_application_agent_tool_が含まれる(self):
        assert "expense_application_agent_tool" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_申請種別に関するキーワードが含まれる(self):
        assert "申請種別" in ORCHESTRATOR_SYSTEM_PROMPT or "BRL-01" in ORCHESTRATOR_SYSTEM_PROMPT
