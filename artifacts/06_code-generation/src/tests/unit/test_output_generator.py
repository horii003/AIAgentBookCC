"""output_generatorの単体テスト"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from unittest.mock import MagicMock, patch, call
from tools.output_generator import (
    generate_transport_expense_form,
    generate_general_expense_form,
    _load_template,
    _save_file,
)


def _make_context(applicant_name="山田太郎", application_date="2026-07-03"):
    ctx = MagicMock()
    ctx.invocation_state = {
        "applicant_name": applicant_name,
        "application_date": application_date,
    }
    return ctx


SECTION = {
    "travel_date": "2026-07-01",
    "departure": "渋谷",
    "destination": "新宿",
    "transport_type": "電車",
    "fare": 200,
    "purpose": "取引先訪問",
}

ITEM = {
    "purchase_date": "2026-07-01",
    "store_name": "文具屋",
    "item_name": "ボールペン",
    "expense_category": "事務用品費",
    "amount": 500,
    "purpose": "業務用",
}


class TestLoadTemplate:
    def test_ファイル不存在でFalseを返す(self):
        with patch("tools.output_generator.os.path.exists", return_value=False):
            ok, msg = _load_template("dummy.xlsx")
        assert ok is False
        assert "見つかりません" in msg

    def test_読み込み例外でFalseを返す(self):
        with patch("tools.output_generator.os.path.exists", return_value=True):
            with patch("tools.output_generator.openpyxl.load_workbook", side_effect=Exception("read error")):
                ok, msg = _load_template("dummy.xlsx")
        assert ok is False
        assert "読み込みに失敗" in msg


class TestSaveFile:
    def test_PermissionErrorでFalseを返す(self, tmp_path):
        wb = MagicMock()
        wb.save.side_effect = PermissionError("denied")
        ok, msg = _save_file(wb, str(tmp_path / "out.xlsx"))
        assert ok is False
        assert "権限" in msg

    def test_IOErrorでFalseを返す(self, tmp_path):
        wb = MagicMock()
        wb.save.side_effect = IOError("io error")
        ok, msg = _save_file(wb, str(tmp_path / "out.xlsx"))
        assert ok is False
        assert "書き込みに失敗" in msg

    def test_想定外例外でFalseを返す(self, tmp_path):
        wb = MagicMock()
        wb.save.side_effect = RuntimeError("unexpected")
        ok, msg = _save_file(wb, str(tmp_path / "out.xlsx"))
        assert ok is False
        assert "予期しない" in msg


class TestGenerateTransportExpenseForm:
    def _run_with_mock_wb(self, sections, total_fare, tmp_path, applicant="山田太郎"):
        ctx = _make_context(applicant_name=applicant)
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws

        with patch("tools.output_generator.os.path.exists", return_value=True):
            with patch("tools.output_generator.openpyxl.load_workbook", return_value=mock_wb):
                with patch("tools.output_generator._OUTPUT_DIR", str(tmp_path)):
                    result = generate_transport_expense_form(
                        sections=sections,
                        total_fare=total_fare,
                        tool_context=ctx,
                    )
        return result, mock_ws

    def test_正常系でsuccessを返す(self, tmp_path):
        result, _ = self._run_with_mock_wb([SECTION], 200, tmp_path)
        assert result["status"] == "success"
        assert "交通費精算申請書" in result["file_path"]

    def test_申請者名と申請日がセルに書き込まれる(self, tmp_path):
        _, ws = self._run_with_mock_wb([SECTION], 200, tmp_path)
        ws.__setitem__.assert_any_call("B3", "山田太郎")

    def test_テンプレート不在でFalseを返す(self):
        ctx = _make_context()
        with patch("tools.output_generator.os.path.exists", return_value=False):
            result = generate_transport_expense_form(
                sections=[SECTION], total_fare=200, tool_context=ctx
            )
        assert result["success"] is False
        assert "見つかりません" in result["message"]

    def test_空sectionsでFalseを返す(self):
        ctx = _make_context()
        with patch("tools.output_generator.os.path.exists", return_value=True):
            result = generate_transport_expense_form(
                sections=[], total_fare=0, tool_context=ctx
            )
        assert result["success"] is False

    def test_負のtotal_fareでFalseを返す(self):
        ctx = _make_context()
        with patch("tools.output_generator.os.path.exists", return_value=True):
            result = generate_transport_expense_form(
                sections=[SECTION], total_fare=-1, tool_context=ctx
            )
        assert result["success"] is False

    def test_ファイル保存失敗でFalseを返す(self, tmp_path):
        ctx = _make_context()
        mock_wb = MagicMock()
        mock_wb.active = MagicMock()
        mock_wb.save.side_effect = PermissionError("denied")

        with patch("tools.output_generator.os.path.exists", return_value=True):
            with patch("tools.output_generator.openpyxl.load_workbook", return_value=mock_wb):
                with patch("tools.output_generator._OUTPUT_DIR", str(tmp_path)):
                    result = generate_transport_expense_form(
                        sections=[SECTION], total_fare=200, tool_context=ctx
                    )
        assert result["success"] is False


class TestGenerateGeneralExpenseForm:
    def _run_with_mock_wb(self, items, total_amount, tmp_path, applicant="山田太郎"):
        ctx = _make_context(applicant_name=applicant)
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws

        with patch("tools.output_generator.os.path.exists", return_value=True):
            with patch("tools.output_generator.openpyxl.load_workbook", return_value=mock_wb):
                with patch("tools.output_generator._OUTPUT_DIR", str(tmp_path)):
                    result = generate_general_expense_form(
                        items=items,
                        total_amount=total_amount,
                        tool_context=ctx,
                    )
        return result, mock_ws

    def test_正常系でsuccessを返す(self, tmp_path):
        result, _ = self._run_with_mock_wb([ITEM], 500, tmp_path)
        assert result["status"] == "success"
        assert "経費精算申請書" in result["file_path"]

    def test_申請者名がセルに書き込まれる(self, tmp_path):
        _, ws = self._run_with_mock_wb([ITEM], 500, tmp_path)
        ws.__setitem__.assert_any_call("B3", "山田太郎")

    def test_テンプレート不在でFalseを返す(self):
        ctx = _make_context()
        with patch("tools.output_generator.os.path.exists", return_value=False):
            result = generate_general_expense_form(
                items=[ITEM], total_amount=500, tool_context=ctx
            )
        assert result["success"] is False
        assert "見つかりません" in result["message"]

    def test_空itemsでFalseを返す(self):
        ctx = _make_context()
        with patch("tools.output_generator.os.path.exists", return_value=True):
            result = generate_general_expense_form(
                items=[], total_amount=0, tool_context=ctx
            )
        assert result["success"] is False

    def test_負のtotal_amountでFalseを返す(self):
        ctx = _make_context()
        with patch("tools.output_generator.os.path.exists", return_value=True):
            result = generate_general_expense_form(
                items=[ITEM], total_amount=-1, tool_context=ctx
            )
        assert result["success"] is False
