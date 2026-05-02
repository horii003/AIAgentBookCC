import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from prompt.prompt_transport import get_transport_agent_system_prompt


class TestPromptTransport:
    def test_returns_non_empty_string(self):
        result = get_transport_agent_system_prompt("2026-05-02")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_embeds_application_date(self):
        result = get_transport_agent_system_prompt("2026-05-02")
        assert "2026-05-02" in result

    def test_computes_deadline_date(self):
        result = get_transport_agent_system_prompt("2026-05-02")
        assert "2026-02-01" in result

    def test_contains_brl14_rule(self):
        result = get_transport_agent_system_prompt("2026-05-02")
        assert "BRL-14" in result

    def test_contains_brl10_rule(self):
        result = get_transport_agent_system_prompt("2026-05-02")
        assert "BRL-10" in result
        assert "10,000" in result

    def test_contains_calculate_transport_fare(self):
        result = get_transport_agent_system_prompt("2026-05-02")
        assert "calculate_transport_fare" in result

    def test_contains_generate_form_tool(self):
        result = get_transport_agent_system_prompt("2026-05-02")
        assert "generate_transport_expense_form" in result

    def test_contains_policy_info(self):
        result = get_transport_agent_system_prompt("2026-05-02")
        assert "BRL-12" in result

    def test_different_dates_produce_different_prompts(self):
        result1 = get_transport_agent_system_prompt("2026-05-02")
        result2 = get_transport_agent_system_prompt("2026-06-01")
        assert result1 != result2
        assert "2026-06-01" in result2

    def test_deadline_boundary(self):
        result = get_transport_agent_system_prompt("2026-04-01")
        assert "2026-01-01" in result
