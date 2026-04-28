"""prompt_expense.py の単体テスト"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from prompt.prompt_expense import build_expense_system_prompt


class TestBuildExpenseSystemPrompt:
    def test_非空文字列を返す(self):
        result = build_expense_system_prompt("2026-04-28")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_申請日が含まれる(self):
        result = build_expense_system_prompt("2026-04-28")
        assert "2026-04-28" in result

    def test_申請期限基準日が含まれる_3ヶ月前(self):
        result = build_expense_system_prompt("2026-04-28")
        assert "2026-01-28" in result

    def test_申請期限基準日が含まれる_年またぎ(self):
        result = build_expense_system_prompt("2026-01-15")
        assert "2025-10-15" in result

    def test_経費精算申請エージェントの役割が含まれる(self):
        result = build_expense_system_prompt("2026-04-28")
        assert "経費精算申請専門エージェント" in result

    def test_業務ポリシーが含まれる(self):
        result = build_expense_system_prompt("2026-04-28")
        assert "BRL-18" in result or "申請期限" in result

    def test_generate_expense_formが含まれる(self):
        result = build_expense_system_prompt("2026-04-28")
        assert "generate_expense_form" in result

    def test_image_readerが含まれる(self):
        result = build_expense_system_prompt("2026-04-28")
        assert "image_reader" in result

    def test_異なる申請日で正しい期限基準日(self):
        result = build_expense_system_prompt("2025-06-01")
        assert "2025-06-01" in result
        assert "2025-03-01" in result
