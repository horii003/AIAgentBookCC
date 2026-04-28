"""prompt_travel.py の単体テスト"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from prompt.prompt_travel import build_travel_system_prompt


class TestBuildTravelSystemPrompt:
    def test_非空文字列を返す(self):
        result = build_travel_system_prompt("2026-04-28")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_申請日が含まれる(self):
        result = build_travel_system_prompt("2026-04-28")
        assert "2026-04-28" in result

    def test_申請期限基準日が含まれる_3ヶ月前(self):
        result = build_travel_system_prompt("2026-04-28")
        assert "2026-01-28" in result

    def test_申請期限基準日が含まれる_月末(self):
        result = build_travel_system_prompt("2026-03-31")
        assert "2025-12-31" in result

    def test_申請期限基準日が含まれる_年またぎ(self):
        result = build_travel_system_prompt("2026-01-15")
        assert "2025-10-15" in result

    def test_交通費精算申請エージェントの役割が含まれる(self):
        result = build_travel_system_prompt("2026-04-28")
        assert "交通費精算申請専門エージェント" in result

    def test_業務ポリシーが含まれる(self):
        result = build_travel_system_prompt("2026-04-28")
        assert "BRL-13" in result or "申請期限" in result

    def test_calculate_travel_expenseが含まれる(self):
        result = build_travel_system_prompt("2026-04-28")
        assert "calculate_travel_expense" in result

    def test_generate_travel_expense_formが含まれる(self):
        result = build_travel_system_prompt("2026-04-28")
        assert "generate_travel_expense_form" in result

    def test_異なる申請日で正しい期限基準日(self):
        result = build_travel_system_prompt("2025-06-01")
        assert "2025-06-01" in result
        assert "2025-03-01" in result
