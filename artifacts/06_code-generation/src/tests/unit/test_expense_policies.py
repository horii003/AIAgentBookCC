import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent_knowledge.expense_policies import get_expense_policies


class TestExpensePolicies:
    def test_returns_non_empty_string(self):
        result = get_expense_policies()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_brl10_high_amount(self):
        result = get_expense_policies()
        assert "BRL-10" in result
        assert "5,000" in result

    def test_contains_brl14_deadline(self):
        result = get_expense_policies()
        assert "BRL-14" in result
        assert "90日" in result

    def test_contains_brl17_expense_categories(self):
        result = get_expense_policies()
        assert "BRL-17" in result
        assert "事務用品費" in result
        assert "宿泊費" in result
        assert "資格精算費" in result
        assert "その他経費" in result

    def test_contains_grd010_confirmation(self):
        result = get_expense_policies()
        assert "GRD-010" in result

    def test_deterministic(self):
        result1 = get_expense_policies()
        result2 = get_expense_policies()
        assert result1 == result2
