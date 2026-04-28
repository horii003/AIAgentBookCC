"""Unit tests for tools/transport_tools.py"""
import json
import os
import pytest
from unittest.mock import patch, MagicMock

from tools.transport_tools import FareDataLoader, _calculate, _fare_loader


class TestFareDataLoader:
    def test_load_train_routes_file_not_found(self, tmp_path):
        loader = FareDataLoader()
        with patch("tools.transport_tools._TRAIN_ROUTES_PATH", str(tmp_path / "missing.json")):
            ok, msg = loader.load_train_routes()
        assert ok is False
        assert "ファイル" in msg or "見つかりません" in msg

    def test_load_train_routes_valid_file(self, tmp_path):
        data = {"渋谷_新宿": 200, "新宿_渋谷": 200}
        fpath = tmp_path / "train_routes.json"
        fpath.write_text(json.dumps(data), encoding="utf-8")
        loader = FareDataLoader()
        with patch("tools.transport_tools._TRAIN_ROUTES_PATH", str(fpath)):
            ok, msg = loader.load_train_routes()
        assert ok is True
        assert loader.train_routes_data == {"渋谷_新宿": 200, "新宿_渋谷": 200}

    def test_load_train_routes_invalid_json(self, tmp_path):
        fpath = tmp_path / "train_routes.json"
        fpath.write_text("not-json", encoding="utf-8")
        loader = FareDataLoader()
        with patch("tools.transport_tools._TRAIN_ROUTES_PATH", str(fpath)):
            ok, msg = loader.load_train_routes()
        assert ok is False
        assert isinstance(msg, str)

    def test_load_fixed_fares_file_not_found(self, tmp_path):
        loader = FareDataLoader()
        with patch("tools.transport_tools._FIXED_FARES_PATH", str(tmp_path / "missing.json")):
            ok, msg = loader.load_fixed_fares()
        assert ok is False

    def test_load_fixed_fares_valid_file(self, tmp_path):
        data = {"バス": 230, "タクシー": 10000, "飛行機": 50000}
        fpath = tmp_path / "fixed_fares.json"
        fpath.write_text(json.dumps(data), encoding="utf-8")
        loader = FareDataLoader()
        with patch("tools.transport_tools._FIXED_FARES_PATH", str(fpath)):
            ok, msg = loader.load_fixed_fares()
        assert ok is True
        assert loader.fixed_fares_data["バス"] == 230


class TestCalculate:
    def setup_method(self):
        self._original_train = _fare_loader.train_routes_data.copy()
        self._original_fixed = _fare_loader.fixed_fares_data.copy()
        _fare_loader.train_routes_data = {
            "渋谷_新宿": 200,
            "新宿_渋谷": 200,
            "東京_品川": 160,
        }
        _fare_loader.fixed_fares_data = {
            "バス": 230,
            "タクシー": 10000,
            "飛行機": 50000,
        }

    def teardown_method(self):
        _fare_loader.train_routes_data = self._original_train
        _fare_loader.fixed_fares_data = self._original_fixed

    def test_train_found(self):
        result = _calculate("電車", "渋谷", "新宿")
        assert result["success"] is True
        assert result["fare"] == 200
        assert "テーブル" in result["calculation_basis"]

    def test_train_not_found(self):
        result = _calculate("電車", "X", "Y")
        assert result["success"] is False
        assert "手動" in result["message"]

    def test_bus(self):
        result = _calculate("バス", "A", "B")
        assert result["success"] is True
        assert result["fare"] == 230
        assert "固定" in result["calculation_basis"]

    def test_taxi(self):
        result = _calculate("タクシー", "A", "B")
        assert result["success"] is True
        assert result["fare"] == 10000

    def test_airplane(self):
        result = _calculate("飛行機", "A", "B")
        assert result["success"] is True
        assert result["fare"] == 50000


class TestCalculateTransportExpenseTool:
    def setup_method(self):
        _fare_loader.train_routes_data = {"渋谷_新宿": 200}
        _fare_loader.fixed_fares_data = {"バス": 230, "タクシー": 10000, "飛行機": 50000}

    def teardown_method(self):
        _fare_loader.train_routes_data = {}
        _fare_loader.fixed_fares_data = {}

    def _make_context(self):
        ctx = MagicMock()
        ctx.invocation_state = {
            "applicant_name": "山田太郎",
            "application_date": "2026-04-28",
            "session_id": "test-session",
        }
        return ctx

    def test_valid_train_route(self):
        from tools.transport_tools import calculate_transport_expense
        ctx = self._make_context()
        result = calculate_transport_expense(
            tool_context=ctx,
            transport_date="2026-04-28",
            departure="渋谷",
            destination="新宿",
            transport_type="電車",
        )
        assert result["success"] is True
        assert result["fare"] == 200

    def test_invalid_transport_type(self):
        from tools.transport_tools import calculate_transport_expense
        ctx = self._make_context()
        result = calculate_transport_expense(
            tool_context=ctx,
            transport_date="2026-04-28",
            departure="渋谷",
            destination="新宿",
            transport_type="自転車",
        )
        assert result["success"] is False
        assert "message" in result

    def test_invalid_date(self):
        from tools.transport_tools import calculate_transport_expense
        ctx = self._make_context()
        result = calculate_transport_expense(
            tool_context=ctx,
            transport_date="invalid-date",
            departure="渋谷",
            destination="新宿",
            transport_type="電車",
        )
        assert result["success"] is False

    def test_train_transport_type_normalization(self):
        from tools.transport_tools import calculate_transport_expense
        ctx = self._make_context()
        result = calculate_transport_expense(
            tool_context=ctx,
            transport_date="2026-04-28",
            departure="渋谷",
            destination="新宿",
            transport_type="train",  # should be normalized to 電車
        )
        assert result["success"] is True
        assert result["fare"] == 200
