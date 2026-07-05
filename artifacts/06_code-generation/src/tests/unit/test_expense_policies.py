"""expense_policiesの単体テスト"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from knowledge.expense_policies import get_expense_rules


class TestGetExpenseRules:
    def test_文字列を返す(self):
        result = get_expense_rules()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_deadline_monthsが含まれる(self):
        result = get_expense_rules(deadline_months=6)
        assert "6" in result

    def test_approval_thresholdが含まれる(self):
        result = get_expense_rules(approval_threshold=8000)
        assert "8" in result

    def test_経費区分が含まれる(self):
        result = get_expense_rules()
        assert "事務用品費" in result
        assert "宿泊費" in result
        assert "資格精算費" in result
        assert "その他経費" in result

    def test_デフォルト値で動作する(self):
        result = get_expense_rules()
        assert "3" in result
        assert "5,000" in result or "5000" in result
