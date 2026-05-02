import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent_knowledge.transport_policies import get_transportation_policies


class TestTransportationPolicies:
    def test_returns_non_empty_string(self):
        result = get_transportation_policies()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_brl10_high_amount(self):
        result = get_transportation_policies()
        assert "BRL-10" in result
        assert "10,000" in result

    def test_contains_brl12_transport_types(self):
        result = get_transportation_policies()
        assert "BRL-12" in result
        assert "電車" in result
        assert "バス" in result
        assert "タクシー" in result
        assert "飛行機" in result

    def test_contains_brl14_deadline(self):
        result = get_transportation_policies()
        assert "BRL-14" in result
        assert "90日" in result

    def test_contains_brl15_station_normalization(self):
        result = get_transportation_policies()
        assert "BRL-15" in result

    def test_deterministic(self):
        result1 = get_transportation_policies()
        result2 = get_transportation_policies()
        assert result1 == result2
