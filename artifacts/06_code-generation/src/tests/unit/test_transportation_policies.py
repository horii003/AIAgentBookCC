"""transportation_policies.py の単体テスト"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from agent_knowledge.transportation_policies import TRANSPORTATION_POLICIES


class TestTransportationPolicies:
    def test_非空文字列である(self):
        assert isinstance(TRANSPORTATION_POLICIES, str)
        assert len(TRANSPORTATION_POLICIES) > 0

    def test_申請期限に関するキーワードが含まれる(self):
        assert "申請期限" in TRANSPORTATION_POLICIES or "BRL-13" in TRANSPORTATION_POLICIES

    def test_上長承認に関するキーワードが含まれる(self):
        assert "上長" in TRANSPORTATION_POLICIES or "BRL-14" in TRANSPORTATION_POLICIES
