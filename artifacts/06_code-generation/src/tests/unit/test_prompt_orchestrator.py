import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from prompt.prompt_orchestrator import get_orchestrator_system_prompt


class TestOrchestratorSystemPrompt:
    def test_returns_non_empty_string(self):
        prompt = get_orchestrator_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_contains_brl01_routing_rule(self):
        prompt = get_orchestrator_system_prompt()
        assert "BRL-01" in prompt

    def test_contains_transport_keywords(self):
        prompt = get_orchestrator_system_prompt()
        assert "交通費精算申請" in prompt
        assert "LNK-001" in prompt

    def test_contains_expense_keywords(self):
        prompt = get_orchestrator_system_prompt()
        assert "経費精算申請" in prompt
        assert "LNK-002" in prompt

    def test_contains_guardrail_grd001(self):
        prompt = get_orchestrator_system_prompt()
        assert "GRD-001" in prompt

    def test_contains_guardrail_grd004(self):
        prompt = get_orchestrator_system_prompt()
        assert "GRD-004" in prompt

    def test_contains_turn_limit_grd005(self):
        prompt = get_orchestrator_system_prompt()
        assert "GRD-005" in prompt

    def test_contains_delegation_prohibition(self):
        prompt = get_orchestrator_system_prompt()
        assert "transport_agent_tool" in prompt
        assert "expense_agent_tool" in prompt

    def test_contains_reset_command(self):
        prompt = get_orchestrator_system_prompt()
        assert "reset" in prompt

    def test_deterministic(self):
        prompt1 = get_orchestrator_system_prompt()
        prompt2 = get_orchestrator_system_prompt()
        assert prompt1 == prompt2
