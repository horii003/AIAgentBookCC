"""output_generator.py の単体テスト"""
import sys
import os
import re
import unittest.mock as mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import tools.output_generator as output_module
from tools.output_generator import generate_travel_expense_form, generate_expense_form

SAMPLE_TRAVEL_ITEMS = [
    {
        "travel_date": "2026-04-28",
        "departure": "渋谷",
        "destination": "新宿",
        "transport_type": "電車",
        "amount": 170,
    },
    {
        "travel_date": "2026-04-28",
        "departure": "新宿",
        "destination": "品川",
        "transport_type": "バス",
        "amount": 230,
    },
]

SAMPLE_EXPENSE_ITEMS = [
    {
        "purchase_date": "2026-04-28",
        "store_name": "文房具店",
        "item_name": "ノート",
        "expense_category": "事務用品費",
        "amount": 500,
    },
]


def _make_tool_context(session_id="test_session_001", applicant_name="田中太郎", application_date="2026-04-28"):
    ctx = mock.MagicMock()
    ctx.invocation_state = {
        "session_id": session_id,
        "applicant_name": applicant_name,
        "application_date": application_date,
    }
    return ctx


class TestGenerateTravelExpenseForm:
    def test_正常_2区間でsuccessTrueとfile_pathが返る(self):
        ctx = _make_tool_context()
        result = generate_travel_expense_form(
            items=SAMPLE_TRAVEL_ITEMS,
            business_purpose="社内会議",
            tool_context=ctx,
        )
        assert result["success"] is True
        assert "file_path" in result
        assert "交通費精算申請書" in result["file_path"]

    def test_正常_ファイルパスにタイムスタンプが含まれる(self):
        ctx = _make_tool_context()
        result = generate_travel_expense_form(
            items=SAMPLE_TRAVEL_ITEMS,
            business_purpose="社内会議",
            tool_context=ctx,
        )
        assert result["success"] is True
        assert re.search(r"\d{14}", result["file_path"])

    def test_正常_session_idがファイルパスに含まれる(self):
        ctx = _make_tool_context(session_id="my_session_abc")
        result = generate_travel_expense_form(
            items=SAMPLE_TRAVEL_ITEMS,
            business_purpose="社内会議",
            tool_context=ctx,
        )
        assert result["success"] is True
        assert "my_session_abc" in result["file_path"]

    def test_異常_テンプレートファイルが存在しない(self):
        orig = output_module.TRAVEL_TEMPLATE_FILE
        output_module.TRAVEL_TEMPLATE_FILE = "nonexistent_template.xlsx"
        try:
            ctx = _make_tool_context()
            result = generate_travel_expense_form(
                items=SAMPLE_TRAVEL_ITEMS,
                business_purpose="社内会議",
                tool_context=ctx,
            )
            assert result["success"] is False
            assert "message" in result
        finally:
            output_module.TRAVEL_TEMPLATE_FILE = orig

    def test_異常_items空リスト(self):
        ctx = _make_tool_context()
        result = generate_travel_expense_form(
            items=[],
            business_purpose="社内会議",
            tool_context=ctx,
        )
        assert result["success"] is False

    def test_異常_business_purposeが空文字(self):
        ctx = _make_tool_context()
        result = generate_travel_expense_form(
            items=SAMPLE_TRAVEL_ITEMS,
            business_purpose="",
            tool_context=ctx,
        )
        assert result["success"] is False


class TestGenerateExpenseForm:
    def test_正常_1件でsuccessTrueとfile_pathが返る(self):
        ctx = _make_tool_context()
        result = generate_expense_form(
            items=SAMPLE_EXPENSE_ITEMS,
            business_purpose="書籍購入",
            tool_context=ctx,
        )
        assert result["success"] is True
        assert "file_path" in result
        assert "経費精算申請書" in result["file_path"]

    def test_正常_expense_categoryが正しく書き込まれる(self):
        ctx = _make_tool_context(session_id="expense_test")
        result = generate_expense_form(
            items=[{
                "purchase_date": "2026-04-28",
                "store_name": "書店",
                "item_name": "技術書",
                "expense_category": "事務用品費",
                "amount": 3000,
            }],
            business_purpose="技術研究",
            tool_context=ctx,
        )
        assert result["success"] is True

        import openpyxl
        wb = openpyxl.load_workbook(result["file_path"])
        ws = wb.active
        assert ws["E7"].value == "事務用品費"

    def test_異常_items空リスト(self):
        ctx = _make_tool_context()
        result = generate_expense_form(
            items=[],
            business_purpose="業務",
            tool_context=ctx,
        )
        assert result["success"] is False

    def test_異常_テンプレートファイルが存在しない(self):
        orig = output_module.EXPENSE_TEMPLATE_FILE
        output_module.EXPENSE_TEMPLATE_FILE = "nonexistent_expense_template.xlsx"
        try:
            ctx = _make_tool_context()
            result = generate_expense_form(
                items=SAMPLE_EXPENSE_ITEMS,
                business_purpose="業務",
                tool_context=ctx,
            )
            assert result["success"] is False
        finally:
            output_module.EXPENSE_TEMPLATE_FILE = orig
