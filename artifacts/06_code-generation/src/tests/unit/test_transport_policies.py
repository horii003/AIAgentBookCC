"""transport_policiesの単体テスト"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from knowledge.transport_policies import get_transport_rules


class TestGetTransportRules:
    def test_文字列を返す(self):
        result = get_transport_rules()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_deadline_monthsが含まれる(self):
        result = get_transport_rules(deadline_months=6)
        assert "6" in result

    def test_approval_thresholdが含まれる(self):
        result = get_transport_rules(approval_threshold=15000)
        assert "15" in result

    def test_デフォルト値で動作する(self):
        result = get_transport_rules()
        assert "3" in result
        assert "10,000" in result or "10000" in result
