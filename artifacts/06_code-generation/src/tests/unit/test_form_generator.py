import sys
import os
import shutil
import tempfile
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unittest.mock import MagicMock
from datetime import date, timedelta


def make_context(applicant_name="田中太郎", application_date="2026-05-02", session_id="test_sess"):
    ctx = MagicMock()
    ctx.invocation_state = {
        "applicant_name": applicant_name,
        "application_date": application_date,
        "session_id": session_id,
    }
    return ctx


TODAY = date.today()
VALID_DATE = (TODAY - timedelta(days=1)).isoformat()
EXPIRED_DATE = (TODAY - timedelta(days=91)).isoformat()

VALID_SEGMENT = {
    "travel_date": VALID_DATE,
    "departure": "渋谷",
    "destination": "新宿",
    "transportation_type": "電車",
    "amount": 200,
    "purpose": "社内会議",
}

VALID_ITEM = {
    "expense_date": VALID_DATE,
    "store_name": "文具屋",
    "amount": 500,
    "item_name": "ボールペン",
    "expense_category": "事務用品費",
    "purpose": "事務用品購入",
}


class TestGenerateTransportExpenseForm:
    def _call(self, segments, context=None):
        import tools.form_generator as mod
        if context is None:
            context = make_context()
        return mod.generate_transport_expense_form.__wrapped__(context, segments)

    def test_success_returns_file_path(self):
        ctx = make_context()
        result = self._call([VALID_SEGMENT], ctx)
        assert result["success"] is True
        assert result["file_path"].endswith(".xlsx")
        assert os.path.exists(result["file_path"])
        os.remove(result["file_path"])

    def test_empty_segments_returns_failure(self):
        result = self._call([])
        assert result["success"] is False
        assert "移動情報" in result["message"]

    def test_missing_required_key(self):
        seg = {k: v for k, v in VALID_SEGMENT.items() if k != "purpose"}
        result = self._call([seg])
        assert result["success"] is False
        assert "必須キー" in result["message"]

    def test_template_not_found(self, tmp_path):
        import tools.form_generator as mod
        import config.settings as settings
        orig = settings.TRANSPORT_TEMPLATE_PATH
        orig_mod = mod.TRANSPORT_TEMPLATE_PATH
        settings.TRANSPORT_TEMPLATE_PATH = str(tmp_path / "nonexistent.xlsx")
        mod.TRANSPORT_TEMPLATE_PATH = str(tmp_path / "nonexistent.xlsx")
        try:
            result = self._call([VALID_SEGMENT])
            assert result["success"] is False
            assert "テンプレート" in result["message"]
        finally:
            settings.TRANSPORT_TEMPLATE_PATH = orig
            mod.TRANSPORT_TEMPLATE_PATH = orig_mod

    def test_expired_travel_date(self):
        seg = dict(VALID_SEGMENT, travel_date=EXPIRED_DATE)
        result = self._call([seg])
        assert result["success"] is False
        assert "90日" in result["message"] or "超過" in result["message"]

    def test_output_contains_applicant_name_in_path(self):
        result = self._call([VALID_SEGMENT])
        if result["success"]:
            assert "田中" in result["file_path"] or "田_中" in result["file_path"] or "田中太郎" in result["file_path"]
            os.remove(result["file_path"])

    def test_multiple_segments(self):
        seg2 = dict(VALID_SEGMENT, departure="新宿", destination="池袋")
        result = self._call([VALID_SEGMENT, seg2])
        assert result["success"] is True
        os.remove(result["file_path"])


class TestGenerateExpenseReimbursementForm:
    def _call(self, items, context=None):
        import tools.form_generator as mod
        if context is None:
            context = make_context()
        return mod.generate_expense_reimbursement_form.__wrapped__(context, items)

    def test_success_returns_file_path(self):
        result = self._call([VALID_ITEM])
        assert result["success"] is True
        assert result["file_path"].endswith(".xlsx")
        assert os.path.exists(result["file_path"])
        os.remove(result["file_path"])

    def test_empty_items_returns_failure(self):
        result = self._call([])
        assert result["success"] is False
        assert "経費情報" in result["message"]

    def test_missing_required_key(self):
        item = {k: v for k, v in VALID_ITEM.items() if k != "purpose"}
        result = self._call([item])
        assert result["success"] is False
        assert "必須キー" in result["message"]

    def test_template_not_found(self, tmp_path):
        import tools.form_generator as mod
        import config.settings as settings
        orig = settings.EXPENSE_TEMPLATE_PATH
        orig_mod = mod.EXPENSE_TEMPLATE_PATH
        settings.EXPENSE_TEMPLATE_PATH = str(tmp_path / "nonexistent.xlsx")
        mod.EXPENSE_TEMPLATE_PATH = str(tmp_path / "nonexistent.xlsx")
        try:
            result = self._call([VALID_ITEM])
            assert result["success"] is False
            assert "テンプレート" in result["message"]
        finally:
            settings.EXPENSE_TEMPLATE_PATH = orig
            mod.EXPENSE_TEMPLATE_PATH = orig_mod

    def test_expired_expense_date(self):
        item = dict(VALID_ITEM, expense_date=EXPIRED_DATE)
        result = self._call([item])
        assert result["success"] is False

    def test_multiple_items(self):
        item2 = dict(VALID_ITEM, item_name="ノート", amount=300)
        result = self._call([VALID_ITEM, item2])
        assert result["success"] is True
        os.remove(result["file_path"])
