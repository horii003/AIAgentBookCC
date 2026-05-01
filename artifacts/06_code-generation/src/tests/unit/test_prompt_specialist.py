"""prompt_transport.py / prompt_expense.py の単体テスト"""
import pytest
from datetime import date, timedelta

from prompt.prompt_transport import build_transport_prompt
from prompt.prompt_expense import build_expense_prompt


class TestBuildTransportPrompt:
    def test_returns_non_empty_string(self):
        """build_transport_prompt() が非空の文字列を返すこと"""
        result = build_transport_prompt("山田太郎", "2026-05-01")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_application_date(self):
        """返却文字列に application_date が含まれること"""
        result = build_transport_prompt("山田太郎", "2026-05-01")
        assert "2026-05-01" in result

    def test_contains_deadline_date(self):
        """返却文字列に deadline_date（3ヶ月前）が含まれること"""
        application_date = "2026-05-01"
        expected_deadline = str(
            date.fromisoformat(application_date) - timedelta(days=90)
        )
        result = build_transport_prompt("山田太郎", application_date)
        assert expected_deadline in result

    def test_deadline_is_90_days_before_application(self):
        """deadline_date が application_date の90日前であること"""
        application_date = "2026-05-01"
        app_dt = date.fromisoformat(application_date)
        expected = str(app_dt - timedelta(days=90))
        result = build_transport_prompt("山田太郎", application_date)
        assert expected in result

    def test_contains_transport_tool_name(self):
        """calculate_transport_fare ツール名が含まれること"""
        result = build_transport_prompt("山田太郎", "2026-05-01")
        assert "calculate_transport_fare" in result

    def test_contains_generate_tool_name(self):
        """generate_transport_application ツール名が含まれること"""
        result = build_transport_prompt("山田太郎", "2026-05-01")
        assert "generate_transport_application" in result

    def test_different_dates_produce_different_prompts(self):
        """異なる application_date で異なるプロンプトが生成されること"""
        result1 = build_transport_prompt("山田太郎", "2026-05-01")
        result2 = build_transport_prompt("山田太郎", "2026-06-01")
        assert result1 != result2


class TestBuildExpensePrompt:
    def test_returns_non_empty_string(self):
        """build_expense_prompt() が非空の文字列を返すこと"""
        result = build_expense_prompt("山田太郎", "2026-05-01")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_application_date(self):
        """返却文字列に application_date が含まれること"""
        result = build_expense_prompt("山田太郎", "2026-05-01")
        assert "2026-05-01" in result

    def test_contains_deadline_date(self):
        """返却文字列に deadline_date（3ヶ月前）が含まれること"""
        application_date = "2026-05-01"
        expected_deadline = str(
            date.fromisoformat(application_date) - timedelta(days=90)
        )
        result = build_expense_prompt("山田太郎", application_date)
        assert expected_deadline in result

    def test_deadline_is_90_days_before_application(self):
        """deadline_date が application_date の90日前であること"""
        application_date = "2026-05-01"
        app_dt = date.fromisoformat(application_date)
        expected = str(app_dt - timedelta(days=90))
        result = build_expense_prompt("山田太郎", application_date)
        assert expected in result

    def test_contains_generate_tool_name(self):
        """generate_expense_application ツール名が含まれること"""
        result = build_expense_prompt("山田太郎", "2026-05-01")
        assert "generate_expense_application" in result

    def test_different_dates_produce_different_prompts(self):
        """異なる application_date で異なるプロンプトが生成されること"""
        result1 = build_expense_prompt("山田太郎", "2026-05-01")
        result2 = build_expense_prompt("山田太郎", "2026-06-01")
        assert result1 != result2
