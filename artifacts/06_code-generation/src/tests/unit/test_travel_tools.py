"""travel_tools.py の単体テスト"""
import sys
import os
import json
import tempfile
import unittest.mock as mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import tools.travel_tools as travel_tools_module
from tools.travel_tools import load_fare_data, calculate_travel_expense


SAMPLE_TRAIN_ROUTES = [
    {"departure": "渋谷", "destination": "新宿", "fare": 170},
    {"departure": "新宿", "destination": "渋谷", "fare": 170},
    {"departure": "東京", "destination": "品川", "fare": 170},
]
SAMPLE_FIXED_FARES = {"バス": 230, "タクシー": 10000, "飛行機": 50000}


def _make_temp_fare_files():
    train_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    )
    json.dump(SAMPLE_TRAIN_ROUTES, train_file, ensure_ascii=False)
    train_file.close()

    fixed_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    )
    json.dump(SAMPLE_FIXED_FARES, fixed_file, ensure_ascii=False)
    fixed_file.close()

    return train_file.name, fixed_file.name


def _setup_module_with_temp_files():
    train_path, fixed_path = _make_temp_fare_files()
    orig_train = travel_tools_module.TRAIN_FARES_FILE
    orig_fixed = travel_tools_module.FIXED_FARES_FILE
    travel_tools_module.TRAIN_FARES_FILE = train_path
    travel_tools_module.FIXED_FARES_FILE = fixed_path
    success, msg = load_fare_data()
    travel_tools_module.TRAIN_FARES_FILE = orig_train
    travel_tools_module.FIXED_FARES_FILE = orig_fixed
    os.unlink(train_path)
    os.unlink(fixed_path)
    return success, msg


def _make_tool_context(session_id="test_session"):
    ctx = mock.MagicMock()
    ctx.invocation_state = {"session_id": session_id}
    return ctx


class TestLoadFareData:
    def setup_method(self):
        travel_tools_module._train_fares = []
        travel_tools_module._fixed_fares = {}

    def test_正常_両ファイルが存在する場合(self):
        success, msg = _setup_module_with_temp_files()
        assert success is True
        assert msg == ""

    def test_正常_train_faresが読み込まれる(self):
        _setup_module_with_temp_files()
        assert len(travel_tools_module._train_fares) == 3

    def test_正常_fixed_faresが読み込まれる(self):
        _setup_module_with_temp_files()
        assert travel_tools_module._fixed_fares.get("バス") == 230

    def test_異常_train_routesが存在しない(self):
        travel_tools_module.TRAIN_FARES_FILE = "nonexistent_train.json"
        orig_fixed = travel_tools_module.FIXED_FARES_FILE
        try:
            success, msg = load_fare_data()
            assert success is False
            assert len(msg) > 0
        finally:
            travel_tools_module.TRAIN_FARES_FILE = "data/templates/train_routes.json"
            travel_tools_module.FIXED_FARES_FILE = orig_fixed

    def test_異常_fixed_faresが存在しない(self):
        train_path, _ = _make_temp_fare_files()
        orig_train = travel_tools_module.TRAIN_FARES_FILE
        travel_tools_module.TRAIN_FARES_FILE = train_path
        travel_tools_module.FIXED_FARES_FILE = "nonexistent_fixed.json"
        try:
            success, msg = load_fare_data()
            assert success is False
            assert len(msg) > 0
        finally:
            travel_tools_module.TRAIN_FARES_FILE = orig_train
            travel_tools_module.FIXED_FARES_FILE = "data/templates/fixed_fares.json"
            os.unlink(train_path)


class TestCalculateTravelExpense:
    def setup_method(self):
        travel_tools_module._train_fares = []
        travel_tools_module._fixed_fares = {}
        _setup_module_with_temp_files()

    def test_正常_電車区間が存在する(self):
        ctx = _make_tool_context()
        result = calculate_travel_expense(
            travel_date="2026-04-28",
            departure="渋谷",
            destination="新宿",
            transport_type="電車",
            tool_context=ctx,
        )
        assert result["success"] is True
        assert result["fare"] == 170
        assert result["calculation_basis"] == "電車経路テーブル参照"

    def test_正常_バス(self):
        ctx = _make_tool_context()
        result = calculate_travel_expense(
            travel_date="2026-04-28",
            departure="A",
            destination="B",
            transport_type="バス",
            tool_context=ctx,
        )
        assert result["success"] is True
        assert result["fare"] == 230
        assert result["calculation_basis"] == "固定運賃参照"

    def test_正常_タクシー(self):
        ctx = _make_tool_context()
        result = calculate_travel_expense(
            travel_date="2026-04-28",
            departure="A",
            destination="B",
            transport_type="タクシー",
            tool_context=ctx,
        )
        assert result["success"] is True
        assert result["fare"] == 10000

    def test_正常_飛行機(self):
        ctx = _make_tool_context()
        result = calculate_travel_expense(
            travel_date="2026-04-28",
            departure="A",
            destination="B",
            transport_type="飛行機",
            tool_context=ctx,
        )
        assert result["success"] is True
        assert result["fare"] == 50000

    def test_正常_transport_typeがtrainに正規化されて電車処理(self):
        ctx = _make_tool_context()
        result = calculate_travel_expense(
            travel_date="2026-04-28",
            departure="渋谷",
            destination="新宿",
            transport_type="train",
            tool_context=ctx,
        )
        assert result["success"] is True
        assert result["fare"] == 170

    def test_異常_存在しない電車区間(self):
        ctx = _make_tool_context()
        result = calculate_travel_expense(
            travel_date="2026-04-28",
            departure="存在しない駅",
            destination="新宿",
            transport_type="電車",
            tool_context=ctx,
        )
        assert result["success"] is False
        assert "手動" in result["message"] or "見つかりません" in result["message"]

    def test_異常_transport_typeが自転車(self):
        ctx = _make_tool_context()
        result = calculate_travel_expense(
            travel_date="2026-04-28",
            departure="渋谷",
            destination="新宿",
            transport_type="自転車",
            tool_context=ctx,
        )
        assert result["success"] is False
        assert "message" in result

    def test_異常_departureが空文字(self):
        ctx = _make_tool_context()
        result = calculate_travel_expense(
            travel_date="2026-04-28",
            departure="",
            destination="新宿",
            transport_type="電車",
            tool_context=ctx,
        )
        assert result["success"] is False

    def test_異常_travel_dateが不正形式(self):
        ctx = _make_tool_context()
        result = calculate_travel_expense(
            travel_date="20260428",
            departure="渋谷",
            destination="新宿",
            transport_type="電車",
            tool_context=ctx,
        )
        assert result["success"] is False

    def test_異常_travel_dateが空文字(self):
        ctx = _make_tool_context()
        result = calculate_travel_expense(
            travel_date="",
            departure="渋谷",
            destination="新宿",
            transport_type="電車",
            tool_context=ctx,
        )
        assert result["success"] is False
