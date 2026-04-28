"""Unit tests for tools/output_generator.py"""
import os
import pytest
from unittest.mock import MagicMock, patch
import openpyxl


def _make_context(session_id="test-session", applicant_name="山田太郎", application_date="2026-04-28"):
    ctx = MagicMock()
    ctx.invocation_state = {
        "session_id": session_id,
        "applicant_name": applicant_name,
        "application_date": application_date,
    }
    return ctx


def _make_transport_segments():
    return [
        {
            "no": 1,
            "transport_date": "2026-04-28",
            "departure": "渋谷",
            "destination": "新宿",
            "transport_type": "電車",
            "amount": 200,
            "business_purpose": "出張",
        }
    ]


def _make_expense_items():
    return [
        {
            "no": 1,
            "purchase_date": "2026-04-28",
            "store_name": "文具屋",
            "item_name": "ボールペン",
            "expense_category": "事務用品費",
            "amount": 500,
            "business_purpose": "業務用",
        }
    ]


class TestGenerateTransportExpenseForm:
    def test_missing_segment_key_returns_error(self):
        from tools.output_generator import generate_transport_expense_form
        ctx = _make_context()
        segments = [{"no": 1, "transport_date": "2026-04-28"}]  # missing keys
        result = generate_transport_expense_form(
            tool_context=ctx, segments=segments, business_purpose="出張"
        )
        assert result["success"] is False
        assert "不足" in result["message"]

    def test_template_not_found_returns_error(self, tmp_path):
        from tools.output_generator import generate_transport_expense_form
        ctx = _make_context()
        with patch("tools.output_generator._TRANSPORT_TEMPLATE_PATH", str(tmp_path / "missing.xlsx")):
            result = generate_transport_expense_form(
                tool_context=ctx,
                segments=_make_transport_segments(),
                business_purpose="出張",
            )
        assert result["success"] is False
        assert "テンプレート" in result["message"]

    def test_valid_generation(self, tmp_path):
        from tools.output_generator import generate_transport_expense_form
        # Create a minimal template
        wb = openpyxl.Workbook()
        ws = wb.active
        template_path = str(tmp_path / "transport_template.xlsx")
        wb.save(template_path)

        ctx = _make_context(session_id="test-session-001")
        with patch("tools.output_generator._TRANSPORT_TEMPLATE_PATH", template_path):
            with patch("tools.output_generator.os.makedirs"):
                with patch("tools.output_generator._save_file", return_value=(True, "data/output/test/file.xlsx")):
                    result = generate_transport_expense_form(
                        tool_context=ctx,
                        segments=_make_transport_segments(),
                        business_purpose="出張",
                    )
        assert result["success"] is True
        assert "file_path" in result

    def test_validation_error_empty_applicant_name(self, tmp_path):
        from tools.output_generator import generate_transport_expense_form
        wb = openpyxl.Workbook()
        template_path = str(tmp_path / "t.xlsx")
        wb.save(template_path)

        ctx = _make_context(applicant_name="")  # empty name → validation error
        with patch("tools.output_generator._TRANSPORT_TEMPLATE_PATH", template_path):
            result = generate_transport_expense_form(
                tool_context=ctx,
                segments=_make_transport_segments(),
                business_purpose="出張",
            )
        assert result["success"] is False


class TestGenerateExpenseForm:
    def test_missing_item_key_returns_error(self):
        from tools.output_generator import generate_expense_form
        ctx = _make_context()
        items = [{"no": 1, "purchase_date": "2026-04-28"}]  # missing keys
        result = generate_expense_form(
            tool_context=ctx, items=items, business_purpose="業務用"
        )
        assert result["success"] is False
        assert "不足" in result["message"]

    def test_template_not_found_returns_error(self, tmp_path):
        from tools.output_generator import generate_expense_form
        ctx = _make_context()
        with patch("tools.output_generator._EXPENSE_TEMPLATE_PATH", str(tmp_path / "missing.xlsx")):
            result = generate_expense_form(
                tool_context=ctx,
                items=_make_expense_items(),
                business_purpose="業務用",
            )
        assert result["success"] is False
        assert "テンプレート" in result["message"]

    def test_valid_generation(self, tmp_path):
        from tools.output_generator import generate_expense_form
        wb = openpyxl.Workbook()
        template_path = str(tmp_path / "expense_template.xlsx")
        wb.save(template_path)

        ctx = _make_context(session_id="test-session-002")
        with patch("tools.output_generator._EXPENSE_TEMPLATE_PATH", template_path):
            with patch("tools.output_generator.os.makedirs"):
                with patch("tools.output_generator._save_file", return_value=(True, "data/output/test/file.xlsx")):
                    result = generate_expense_form(
                        tool_context=ctx,
                        items=_make_expense_items(),
                        business_purpose="業務用",
                    )
        assert result["success"] is True
        assert "file_path" in result


class TestSaveFile:
    def test_save_success(self, tmp_path):
        from tools.output_generator import _save_file
        wb = openpyxl.Workbook()
        path = str(tmp_path / "test.xlsx")
        ok, result = _save_file(wb, path)
        assert ok is True
        assert result == path
        assert os.path.exists(path)

    def test_save_permission_error(self, tmp_path):
        from tools.output_generator import _save_file
        wb = openpyxl.Workbook()
        with patch.object(wb, "save", side_effect=PermissionError("denied")):
            ok, msg = _save_file(wb, "some/path.xlsx")
        assert ok is False
        assert isinstance(msg, str)
