"""Unit tests for prompt modules and agent_knowledge modules"""
import pytest

from prompt.prompt_orchestrator import ORCHESTRATOR_SYSTEM_PROMPT
from prompt.prompt_transport_agent import build_transport_agent_system_prompt, _calc_deadline_date as transport_deadline
from prompt.prompt_expense_agent import build_expense_agent_system_prompt, _calc_deadline_date as expense_deadline
from agent_knowledge import transportation_policies as tp
from agent_knowledge import receipt_policies as rp


# ---- ORCHESTRATOR_SYSTEM_PROMPT ----

class TestOrchestratorPrompt:
    def test_is_string(self):
        assert isinstance(ORCHESTRATOR_SYSTEM_PROMPT, str)

    def test_not_empty(self):
        assert len(ORCHESTRATOR_SYSTEM_PROMPT) > 100

    def test_contains_role(self):
        assert "申請受付窓口エージェント" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_contains_tool_names(self):
        assert "transport_application_agent_tool" in ORCHESTRATOR_SYSTEM_PROMPT
        assert "expense_application_agent_tool" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_contains_brl01(self):
        assert "BRL-01" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_contains_brl02(self):
        assert "BRL-02" in ORCHESTRATOR_SYSTEM_PROMPT


# ---- transportation_policies ----

class TestTransportationPolicies:
    def test_deadline_months(self):
        assert tp.DEADLINE_MONTHS == 3

    def test_manager_approval_threshold(self):
        assert tp.MANAGER_APPROVAL_THRESHOLD == 10000

    def test_allowed_transport_types(self):
        assert "電車" in tp.ALLOWED_TRANSPORT_TYPES
        assert "バス" in tp.ALLOWED_TRANSPORT_TYPES
        assert "タクシー" in tp.ALLOWED_TRANSPORT_TYPES
        assert "飛行機" in tp.ALLOWED_TRANSPORT_TYPES


# ---- receipt_policies ----

class TestReceiptPolicies:
    def test_deadline_months(self):
        assert rp.DEADLINE_MONTHS == 3

    def test_manager_approval_threshold(self):
        assert rp.MANAGER_APPROVAL_THRESHOLD == 5000

    def test_expense_categories(self):
        assert "事務用品費" in rp.EXPENSE_CATEGORIES
        assert "宿泊費" in rp.EXPENSE_CATEGORIES
        assert "資格精算費" in rp.EXPENSE_CATEGORIES
        assert "その他経費" in rp.EXPENSE_CATEGORIES


# ---- build_transport_agent_system_prompt ----

class TestBuildTransportAgentSystemPrompt:
    def test_returns_string(self):
        result = build_transport_agent_system_prompt("2026-04-28")
        assert isinstance(result, str)

    def test_contains_application_date(self):
        result = build_transport_agent_system_prompt("2026-04-28")
        assert "2026-04-28" in result

    def test_contains_deadline_date(self):
        result = build_transport_agent_system_prompt("2026-04-28")
        # 3 months before 2026-04-28 is 2026-01-28
        assert "2026-01-28" in result

    def test_contains_manager_threshold(self):
        result = build_transport_agent_system_prompt("2026-04-28")
        assert str(tp.MANAGER_APPROVAL_THRESHOLD) in result

    def test_contains_deadline_months(self):
        result = build_transport_agent_system_prompt("2026-04-28")
        assert str(tp.DEADLINE_MONTHS) in result

    def test_contains_role(self):
        result = build_transport_agent_system_prompt("2026-04-28")
        assert "交通費精算申請エージェント" in result

    def test_invalid_date_does_not_raise(self):
        result = build_transport_agent_system_prompt("invalid")
        assert isinstance(result, str)


class TestCalcDeadlineDateTransport:
    def test_3_months_before(self):
        assert transport_deadline("2026-04-28") == "2026-01-28"

    def test_month_boundary(self):
        assert transport_deadline("2026-03-31") == "2025-12-31"

    def test_invalid_returns_empty(self):
        assert transport_deadline("not-a-date") == ""


# ---- build_expense_agent_system_prompt ----

class TestBuildExpenseAgentSystemPrompt:
    def test_returns_string(self):
        result = build_expense_agent_system_prompt("2026-04-28")
        assert isinstance(result, str)

    def test_contains_application_date(self):
        result = build_expense_agent_system_prompt("2026-04-28")
        assert "2026-04-28" in result

    def test_contains_deadline_date(self):
        result = build_expense_agent_system_prompt("2026-04-28")
        assert "2026-01-28" in result

    def test_contains_manager_threshold(self):
        result = build_expense_agent_system_prompt("2026-04-28")
        assert str(rp.MANAGER_APPROVAL_THRESHOLD) in result

    def test_contains_expense_categories(self):
        result = build_expense_agent_system_prompt("2026-04-28")
        assert "事務用品費" in result
        assert "宿泊費" in result

    def test_contains_role(self):
        result = build_expense_agent_system_prompt("2026-04-28")
        assert "経費精算申請エージェント" in result

    def test_invalid_date_does_not_raise(self):
        result = build_expense_agent_system_prompt("invalid")
        assert isinstance(result, str)
