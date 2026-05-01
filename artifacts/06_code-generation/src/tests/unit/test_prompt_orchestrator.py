"""prompt_orchestrator.py の単体テスト"""
from prompt.prompt_orchestrator import ORCHESTRATOR_SYSTEM_PROMPT


class TestOrchestratorSystemPrompt:
    def test_is_non_empty_string(self):
        """ORCHESTRATOR_SYSTEM_PROMPT が非空の文字列であること"""
        assert isinstance(ORCHESTRATOR_SYSTEM_PROMPT, str)
        assert len(ORCHESTRATOR_SYSTEM_PROMPT) > 0

    def test_contains_transport_agent_tool(self):
        """handle_transport_expense_application が含まれること"""
        assert "handle_transport_expense_application" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_contains_expense_agent_tool(self):
        """handle_expense_application が含まれること"""
        assert "handle_expense_application" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_contains_brl_01(self):
        """BRL-01 が含まれること"""
        assert "BRL-01" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_contains_brl_04(self):
        """BRL-04 が含まれること"""
        assert "BRL-04" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_contains_brl_14(self):
        """BRL-14 が含まれること"""
        assert "BRL-14" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_contains_lnk_references(self):
        """LNK-001/LNK-002 委譲への言及が含まれること"""
        assert "LNK-001" in ORCHESTRATOR_SYSTEM_PROMPT
        assert "LNK-002" in ORCHESTRATOR_SYSTEM_PROMPT
