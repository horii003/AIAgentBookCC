"""receipt_policies.py の単体テスト"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from agent_knowledge.receipt_policies import RECEIPT_POLICIES


class TestReceiptPolicies:
    def test_非空文字列である(self):
        assert isinstance(RECEIPT_POLICIES, str)
        assert len(RECEIPT_POLICIES) > 0

    def test_領収書に関するキーワードが含まれる(self):
        assert "領収書" in RECEIPT_POLICIES or "BRL-17" in RECEIPT_POLICIES
