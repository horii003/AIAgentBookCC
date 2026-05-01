"""application_generator.py の単体テスト"""
import os
import pytest
from unittest.mock import patch, MagicMock, call
from strands.types.tools import ToolContext

from tools.application_generator import generate_transport_application, generate_expense_application


def _make_tool_context(applicant_name="山田太郎", application_date="2026-05-01", session_id="test-session"):
    ctx = MagicMock(spec=ToolContext)
    ctx.invocation_state = {
        "applicant_name": applicant_name,
        "application_date": application_date,
        "session_id": session_id,
    }
    return ctx


VALID_TRANSPORT_ITEMS = {
    "segments": [
        {
            "travel_date": "2026-04-15",
            "departure": "渋谷",
            "destination": "品川",
            "transport_type": "電車",
            "fare": 250,
            "business_purpose": "顧客訪問",
        }
    ]
}

VALID_EXPENSE_ITEMS = {
    "expenses": [
        {
            "purchase_date": "2026-04-15",
            "store_name": "文具店",
            "item_name": "ボールペン",
            "expense_category": "事務用品費",
            "amount": 500,
            "business_purpose": "業務用",
        }
    ]
}


class TestGenerateTransportApplication:
    def test_missing_segments_key_returns_failure(self):
        """collected_items に 'segments' キーがない場合に success=False が返却されること"""
        ctx = _make_tool_context()
        result = generate_transport_application({"wrong_key": []}, ctx)
        assert result["success"] is False
        assert result["file_path"] is None
        assert isinstance(result["message"], str)

    def test_template_not_found_returns_failure(self):
        """テンプレートファイルが存在しない場合に success=False が返却されること"""
        ctx = _make_tool_context()
        with patch("os.path.exists", return_value=False):
            result = generate_transport_application(VALID_TRANSPORT_ITEMS, ctx)
        assert result["success"] is False
        assert result["file_path"] is None
        assert isinstance(result["message"], str)

    def test_successful_generation_returns_file_path(self):
        """正常な入力で Excel ファイルが生成され file_path が返却されること"""
        ctx = _make_tool_context()
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws

        with patch("os.path.exists", return_value=True), \
             patch("openpyxl.load_workbook", return_value=mock_wb), \
             patch("os.makedirs"), \
             patch.object(mock_wb, "save"):
            result = generate_transport_application(VALID_TRANSPORT_ITEMS, ctx)

        assert result["success"] is True
        assert result["file_path"] is not None
        assert "山田太郎" in result["file_path"]
        assert result["message"] is None

    def test_applicant_name_written_to_b3(self):
        """申請者名が B3 セルに書き込まれること"""
        ctx = _make_tool_context(applicant_name="鈴木花子")
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws

        with patch("os.path.exists", return_value=True), \
             patch("openpyxl.load_workbook", return_value=mock_wb), \
             patch("os.makedirs"), \
             patch.object(mock_wb, "save"):
            generate_transport_application(VALID_TRANSPORT_ITEMS, ctx)

        mock_ws.__setitem__.assert_any_call("B3", "鈴木花子")

    def test_no_column_written_for_approval_status(self):
        """H列（承認状況）に空文字が書き込まれること"""
        ctx = _make_tool_context()
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws

        with patch("os.path.exists", return_value=True), \
             patch("openpyxl.load_workbook", return_value=mock_wb), \
             patch("os.makedirs"), \
             patch.object(mock_wb, "save"):
            generate_transport_application(VALID_TRANSPORT_ITEMS, ctx)

        mock_ws.__setitem__.assert_any_call("H7", "")

    def test_row_number_starts_at_7(self):
        """明細行が A7 から始まること（No=1）"""
        ctx = _make_tool_context()
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws

        with patch("os.path.exists", return_value=True), \
             patch("openpyxl.load_workbook", return_value=mock_wb), \
             patch("os.makedirs"), \
             patch.object(mock_wb, "save"):
            generate_transport_application(VALID_TRANSPORT_ITEMS, ctx)

        mock_ws.__setitem__.assert_any_call("A7", 1)

    def test_empty_segments_returns_failure(self):
        """segments が空リストで ValidationError による success=False が返却されること"""
        ctx = _make_tool_context()
        with patch("os.path.exists", return_value=True):
            result = generate_transport_application({"segments": []}, ctx)
        assert result["success"] is False
        assert isinstance(result["message"], str)

    def test_ioerror_on_save_returns_tuple(self):
        """ファイル保存時に IOError が発生した場合にタプルが返却されること"""
        ctx = _make_tool_context()
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws

        with patch("os.path.exists", return_value=True), \
             patch("openpyxl.load_workbook", return_value=mock_wb), \
             patch("os.makedirs"), \
             patch.object(mock_wb, "save", side_effect=IOError("disk full")):
            result = generate_transport_application(VALID_TRANSPORT_ITEMS, ctx)

        assert result is not None

    def test_output_path_contains_session_id(self):
        """出力ファイルパスにセッション ID が含まれること"""
        ctx = _make_tool_context(session_id="my-session-123")
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws

        with patch("os.path.exists", return_value=True), \
             patch("openpyxl.load_workbook", return_value=mock_wb), \
             patch("os.makedirs"), \
             patch.object(mock_wb, "save"):
            result = generate_transport_application(VALID_TRANSPORT_ITEMS, ctx)

        assert "my-session-123" in result["file_path"]


class TestGenerateExpenseApplication:
    def test_missing_expenses_key_returns_failure(self):
        """collected_items に 'expenses' キーがない場合に success=False が返却されること"""
        ctx = _make_tool_context()
        result = generate_expense_application({"wrong_key": []}, ctx)
        assert result["success"] is False
        assert result["file_path"] is None
        assert isinstance(result["message"], str)

    def test_template_not_found_returns_failure(self):
        """テンプレートファイルが存在しない場合に success=False が返却されること"""
        ctx = _make_tool_context()
        with patch("os.path.exists", return_value=False):
            result = generate_expense_application(VALID_EXPENSE_ITEMS, ctx)
        assert result["success"] is False

    def test_successful_generation_returns_file_path(self):
        """正常な入力で Excel ファイルが生成され file_path が返却されること"""
        ctx = _make_tool_context()
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws

        with patch("os.path.exists", return_value=True), \
             patch("openpyxl.load_workbook", return_value=mock_wb), \
             patch("os.makedirs"), \
             patch.object(mock_wb, "save"):
            result = generate_expense_application(VALID_EXPENSE_ITEMS, ctx)

        assert result["success"] is True
        assert result["file_path"] is not None
        assert result["message"] is None

    def test_empty_expenses_returns_failure(self):
        """expenses が空リストで ValidationError による success=False が返却されること"""
        ctx = _make_tool_context()
        with patch("os.path.exists", return_value=True):
            result = generate_expense_application({"expenses": []}, ctx)
        assert result["success"] is False

    def test_applicant_name_written_to_b3(self):
        """申請者名が B3 セルに書き込まれること"""
        ctx = _make_tool_context(applicant_name="田中一郎")
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws

        with patch("os.path.exists", return_value=True), \
             patch("openpyxl.load_workbook", return_value=mock_wb), \
             patch("os.makedirs"), \
             patch.object(mock_wb, "save"):
            generate_expense_application(VALID_EXPENSE_ITEMS, ctx)

        mock_ws.__setitem__.assert_any_call("B3", "田中一郎")

    def test_output_path_contains_session_id(self):
        """出力ファイルパスにセッション ID が含まれること"""
        ctx = _make_tool_context(session_id="expense-session-456")
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws

        with patch("os.path.exists", return_value=True), \
             patch("openpyxl.load_workbook", return_value=mock_wb), \
             patch("os.makedirs"), \
             patch.object(mock_wb, "save"):
            result = generate_expense_application(VALID_EXPENSE_ITEMS, ctx)

        assert "expense-session-456" in result["file_path"]
