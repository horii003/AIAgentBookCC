"""receipt_policies.py の単体テスト"""
from agent_knowledge.receipt_policies import get_receipt_policies


class TestGetReceiptPolicies:
    def test_returns_non_empty_string(self):
        """get_receipt_policies() が非空の文字列を返すこと"""
        result = get_receipt_policies()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_brl_07(self):
        """返却文字列に BRL-07 が含まれること"""
        result = get_receipt_policies()
        assert "BRL-07" in result

    def test_contains_brl_09(self):
        """返却文字列に BRL-09 が含まれること"""
        result = get_receipt_policies()
        assert "BRL-09" in result

    def test_contains_brl_11(self):
        """返却文字列に BRL-11 が含まれること"""
        result = get_receipt_policies()
        assert "BRL-11" in result

    def test_contains_brl_12(self):
        """返却文字列に BRL-12 が含まれること"""
        result = get_receipt_policies()
        assert "BRL-12" in result

    def test_contains_brl_13(self):
        """返却文字列に BRL-13 が含まれること"""
        result = get_receipt_policies()
        assert "BRL-13" in result

    def test_idempotent(self):
        """複数回呼び出しても同じ値を返すこと"""
        assert get_receipt_policies() == get_receipt_policies()
