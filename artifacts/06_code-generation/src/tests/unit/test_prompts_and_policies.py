# 参照: DD-02a/b/c 各エージェント詳細設計書
"""prompt/とknowledge/の単体テスト"""
import sys
import os
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestPromptOrchestrator:
    """prompt_orchestrator のテスト"""

    def test_prompt_not_empty(self):
        """ORCHESTRATOR_SYSTEM_PROMPTが空でないこと。"""
        from prompt.prompt_orchestrator import ORCHESTRATOR_SYSTEM_PROMPT
        assert isinstance(ORCHESTRATOR_SYSTEM_PROMPT, str)
        assert len(ORCHESTRATOR_SYSTEM_PROMPT) > 0

    def test_prompt_contains_required_sections(self):
        """プロンプトに必須セクション（役割・申請種別判断ルール・処理フロー・禁止事項）が含まれること。"""
        from prompt.prompt_orchestrator import ORCHESTRATOR_SYSTEM_PROMPT
        assert "役割" in ORCHESTRATOR_SYSTEM_PROMPT
        assert "申請種別判断ルール" in ORCHESTRATOR_SYSTEM_PROMPT
        assert "処理フロー" in ORCHESTRATOR_SYSTEM_PROMPT
        assert "禁止事項" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_prompt_contains_brl01(self):
        """プロンプトにBRL-01キーワードが含まれること。"""
        from prompt.prompt_orchestrator import ORCHESTRATOR_SYSTEM_PROMPT
        assert "BRL-01" in ORCHESTRATOR_SYSTEM_PROMPT


class TestPromptTransport:
    """prompt_transport のテスト"""

    def test_not_empty(self):
        """get_transport_system_prompt()が空でないこと。"""
        from prompt.prompt_transport import get_transport_system_prompt
        result = get_transport_system_prompt("山田太郎", "2026-05-06")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_applicant_name(self):
        """戻り値にapplicant_nameが含まれること。"""
        from prompt.prompt_transport import get_transport_system_prompt
        result = get_transport_system_prompt("山田太郎", "2026-05-06")
        assert "山田太郎" in result

    def test_contains_application_date(self):
        """戻り値にapplication_dateが含まれること。"""
        from prompt.prompt_transport import get_transport_system_prompt
        result = get_transport_system_prompt("山田太郎", "2026-05-06")
        assert "2026-05-06" in result

    def test_contains_deadline_date(self):
        """戻り値にdeadline_date（申請日の90日前）が含まれること。"""
        from prompt.prompt_transport import get_transport_system_prompt
        result = get_transport_system_prompt("山田太郎", "2026-05-06")
        # 90日前は2026-02-05
        assert "2026-02-05" in result

    def test_contains_transportation_policies(self):
        """戻り値にtransportation_policiesの内容が含まれること。"""
        from prompt.prompt_transport import get_transport_system_prompt
        from knowledge.transportation_policies import get_transportation_policies
        result = get_transport_system_prompt("山田太郎", "2026-05-06")
        policies = get_transportation_policies()
        # ポリシーの一部が含まれること（ポリシーが長いため部分一致で確認）
        assert "BRL-11" in result or "上長承認" in result


class TestPromptExpense:
    """prompt_expense のテスト"""

    def test_not_empty(self):
        """get_expense_system_prompt()が空でないこと。"""
        from prompt.prompt_expense import get_expense_system_prompt
        result = get_expense_system_prompt("山田太郎", "2026-05-06")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_applicant_name(self):
        """戻り値にapplicant_nameが含まれること。"""
        from prompt.prompt_expense import get_expense_system_prompt
        result = get_expense_system_prompt("山田太郎", "2026-05-06")
        assert "山田太郎" in result

    def test_contains_deadline_date(self):
        """戻り値にdeadline_date（申請日の90日前）が含まれること。"""
        from prompt.prompt_expense import get_expense_system_prompt
        result = get_expense_system_prompt("山田太郎", "2026-05-06")
        assert "2026-02-05" in result

    def test_contains_receipt_policies(self):
        """戻り値にreceipt_policiesの内容が含まれること。"""
        from prompt.prompt_expense import get_expense_system_prompt
        result = get_expense_system_prompt("山田太郎", "2026-05-06")
        assert "BRL-18" in result or "上長承認" in result

    def test_contains_tool001_prohibition(self):
        """戻り値にTOOL-001またはcalculate_transport_fareの禁止指示が含まれること。"""
        from prompt.prompt_expense import get_expense_system_prompt
        result = get_expense_system_prompt("山田太郎", "2026-05-06")
        assert "TOOL-001" in result or "calculate_transport_fare" in result


class TestTransportationPolicies:
    """transportation_policies のテスト"""

    def test_not_empty(self):
        """get_transportation_policies()が空でないこと。"""
        from knowledge.transportation_policies import get_transportation_policies
        result = get_transportation_policies()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_approval_amount(self):
        """戻り値に上長承認基準（10,000円）に関する記述が含まれること。"""
        from knowledge.transportation_policies import get_transportation_policies
        result = get_transportation_policies()
        assert "10,000" in result or "10000" in result

    def test_contains_deadline_days(self):
        """戻り値に申請期限（90日）に関する記述が含まれること。"""
        from knowledge.transportation_policies import get_transportation_policies
        result = get_transportation_policies()
        assert "90日" in result


class TestReceiptPolicies:
    """receipt_policies のテスト"""

    def test_not_empty(self):
        """get_receipt_policies()が空でないこと。"""
        from knowledge.receipt_policies import get_receipt_policies
        result = get_receipt_policies()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_approval_amount(self):
        """戻り値に上長承認基準（5,000円）に関する記述が含まれること。"""
        from knowledge.receipt_policies import get_receipt_policies
        result = get_receipt_policies()
        assert "5,000" in result or "5000" in result

    def test_contains_deadline_days(self):
        """戻り値に申請期限（90日）に関する記述が含まれること。"""
        from knowledge.receipt_policies import get_receipt_policies
        result = get_receipt_policies()
        assert "90日" in result

    def test_contains_expense_categories(self):
        """戻り値に経費区分（事務用品費/宿泊費/資格精算費/その他経費）に関する記述が含まれること。"""
        from knowledge.receipt_policies import get_receipt_policies
        result = get_receipt_policies()
        assert "事務用品費" in result
        assert "宿泊費" in result
        assert "資格精算費" in result
        assert "その他経費" in result
