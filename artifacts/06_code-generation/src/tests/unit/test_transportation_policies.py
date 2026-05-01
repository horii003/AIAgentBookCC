"""transportation_policies.py の単体テスト"""
from agent_knowledge.transportation_policies import get_transportation_policies


class TestGetTransportationPolicies:
    def test_returns_non_empty_string(self):
        """get_transportation_policies() が非空の文字列を返すこと"""
        result = get_transportation_policies()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_brl_05(self):
        """返却文字列に BRL-05 が含まれること"""
        result = get_transportation_policies()
        assert "BRL-05" in result

    def test_contains_brl_06(self):
        """返却文字列に BRL-06 が含まれること"""
        result = get_transportation_policies()
        assert "BRL-06" in result

    def test_contains_brl_07(self):
        """返却文字列に BRL-07 が含まれること"""
        result = get_transportation_policies()
        assert "BRL-07" in result

    def test_contains_brl_08(self):
        """返却文字列に BRL-08 が含まれること"""
        result = get_transportation_policies()
        assert "BRL-08" in result

    def test_contains_brl_10(self):
        """返却文字列に BRL-10 が含まれること"""
        result = get_transportation_policies()
        assert "BRL-10" in result

    def test_contains_brl_11(self):
        """返却文字列に BRL-11 が含まれること"""
        result = get_transportation_policies()
        assert "BRL-11" in result

    def test_contains_brl_12(self):
        """返却文字列に BRL-12 が含まれること"""
        result = get_transportation_policies()
        assert "BRL-12" in result

    def test_contains_brl_13(self):
        """返却文字列に BRL-13 が含まれること"""
        result = get_transportation_policies()
        assert "BRL-13" in result

    def test_contains_brl_16(self):
        """返却文字列に BRL-16 が含まれること"""
        result = get_transportation_policies()
        assert "BRL-16" in result

    def test_contains_brl_17(self):
        """返却文字列に BRL-17 が含まれること"""
        result = get_transportation_policies()
        assert "BRL-17" in result

    def test_contains_brl_18(self):
        """返却文字列に BRL-18 が含まれること"""
        result = get_transportation_policies()
        assert "BRL-18" in result

    def test_idempotent(self):
        """複数回呼び出しても同じ値を返すこと"""
        assert get_transportation_policies() == get_transportation_policies()
