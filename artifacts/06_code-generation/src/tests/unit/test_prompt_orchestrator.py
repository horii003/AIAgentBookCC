"""prompt_orchestratorの単体テスト"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from prompt.prompt_orchestrator import ORCHESTRATOR_SYSTEM_PROMPT


class TestOrchestratorSystemPrompt:
    def test_文字列型である(self):
        assert isinstance(ORCHESTRATOR_SYSTEM_PROMPT, str)

    def test_空ではない(self):
        assert len(ORCHESTRATOR_SYSTEM_PROMPT.strip()) > 0

    def test_transport_application_agentが含まれる(self):
        assert "transport_application_agent" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_expense_application_agentが含まれる(self):
        assert "expense_application_agent" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_役割定義が含まれる(self):
        assert "申請受付窓口エージェント" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_振り分け先が明示されている(self):
        assert "交通費精算申請" in ORCHESTRATOR_SYSTEM_PROMPT
        assert "経費精算申請" in ORCHESTRATOR_SYSTEM_PROMPT
