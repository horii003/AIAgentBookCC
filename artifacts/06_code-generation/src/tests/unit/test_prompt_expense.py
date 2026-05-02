import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from prompt.prompt_expense import get_expense_agent_system_prompt


class TestPromptExpense:
    def test_returns_non_empty_string(self):
        result = get_expense_agent_system_prompt("2026-05-02")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_embeds_application_date(self):
        result = get_expense_agent_system_prompt("2026-05-02")
        assert "2026-05-02" in result

    def test_computes_deadline_date(self):
        result = get_expense_agent_system_prompt("2026-05-02")
        assert "2026-02-01" in result

    def test_contains_brl14_rule(self):
        result = get_expense_agent_system_prompt("2026-05-02")
        assert "BRL-14" in result

    def test_contains_brl10_rule(self):
        result = get_expense_agent_system_prompt("2026-05-02")
        assert "BRL-10" in result
        assert "5,000" in result

    def test_contains_image_reader(self):
        result = get_expense_agent_system_prompt("2026-05-02")
        assert "image_reader" in result

    def test_contains_generate_form_tool(self):
        result = get_expense_agent_system_prompt("2026-05-02")
        assert "generate_expense_reimbursement_form" in result

    def test_contains_brl17_expense_categories(self):
        result = get_expense_agent_system_prompt("2026-05-02")
        assert "BRL-17" in result
        assert "事務用品費" in result
        assert "宿泊費" in result
        assert "資格精算費" in result

    def test_contains_grd010_prohibition(self):
        result = get_expense_agent_system_prompt("2026-05-02")
        assert "GRD-010" in result

    def test_different_dates_produce_different_prompts(self):
        result1 = get_expense_agent_system_prompt("2026-05-02")
        result2 = get_expense_agent_system_prompt("2026-06-01")
        assert result1 != result2

    def test_contains_policy_info(self):
        result = get_expense_agent_system_prompt("2026-05-02")
        assert "GRD-010" in result
