"""transport_calculator.py の単体テスト"""
import json
import os
import pytest
from unittest.mock import patch, mock_open, MagicMock

from tools.transport_calculator import calculate_transport_fare


VALID_TRAIN_ROUTES = json.dumps({
    "routes": [
        {"departure": "渋谷", "destination": "品川", "fare": 250},
        {"departure": "品川", "destination": "渋谷", "fare": 250},
        {"departure": "新宿", "destination": "東京", "fare": 220},
    ]
})

VALID_FIXED_FARES = json.dumps({
    "バス": 230,
    "タクシー": 1500,
    "飛行機": 15000,
})


def _mock_train_file(content=VALID_TRAIN_ROUTES):
    return mock_open(read_data=content)


def _mock_fixed_file(content=VALID_FIXED_FARES):
    return mock_open(read_data=content)


class TestCalculateTransportFareTrain:
    def test_existing_route_returns_fare(self):
        """登録済み経路（渋谷→品川）で運賃が返却されること"""
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", _mock_train_file()):
            result = calculate_transport_fare("電車", "渋谷", "品川", "2026-05-01")
        assert result["calculable"] is True
        assert result["fare"] == 250
        assert result["success"] is True
        assert result["message"] is None

    def test_station_name_with_suffix_is_normalized(self):
        """「渋谷駅」が「渋谷」に正規化されて検索されること"""
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", _mock_train_file()):
            result = calculate_transport_fare("電車", "渋谷駅", "品川駅", "2026-05-01")
        assert result["calculable"] is True
        assert result["fare"] == 250

    def test_train_type_normalized_from_english(self):
        """「train」が「電車」に正規化されて処理されること"""
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", _mock_train_file()):
            result = calculate_transport_fare("train", "渋谷", "品川", "2026-05-01")
        assert result["calculable"] is True
        assert result["fare"] == 250

    def test_nonexistent_route_returns_calculable_false(self):
        """未登録経路で calculable=False・success=True が返却されること"""
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", _mock_train_file()):
            result = calculate_transport_fare("電車", "上野", "代々木", "2026-05-01")
        assert result["calculable"] is False
        assert result["fare"] is None
        assert result["success"] is True
        assert result["message"] is None

    def test_missing_train_routes_file_returns_error_tuple(self):
        """train_routes.json が存在しない場合に success=False が返却されること"""
        with patch("os.path.exists", return_value=False):
            result = calculate_transport_fare("電車", "渋谷", "品川", "2026-05-01")
        assert result["success"] is False
        assert result["calculable"] is False
        assert result["fare"] is None
        assert isinstance(result["message"], str)

    def test_file_read_error_returns_failure(self):
        """ファイル読み込み中に Exception 発生時に success=False が返却されること"""
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", side_effect=IOError("read error")):
            result = calculate_transport_fare("電車", "渋谷", "品川", "2026-05-01")
        assert result["success"] is False
        assert isinstance(result["message"], str)

    def test_invalid_schema_returns_failure(self):
        """スキーマ不正の train_routes.json で success=False が返却されること"""
        bad_json = json.dumps({"invalid_key": []})
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=bad_json)):
            result = calculate_transport_fare("電車", "渋谷", "品川", "2026-05-01")
        assert result["success"] is False
        assert result["calculable"] is False


class TestCalculateTransportFareFixed:
    def test_bus_fare_returned(self):
        """バス固定運賃が返却されること"""
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", _mock_fixed_file()):
            result = calculate_transport_fare("バス", "A地点", "B地点", "2026-05-01")
        assert result["calculable"] is True
        assert result["fare"] == 230
        assert result["success"] is True

    def test_taxi_fare_returned(self):
        """タクシー固定運賃が返却されること"""
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", _mock_fixed_file()):
            result = calculate_transport_fare("タクシー", "A地点", "B地点", "2026-05-01")
        assert result["calculable"] is True
        assert result["fare"] == 1500

    def test_airplane_fare_returned(self):
        """飛行機固定運賃が返却されること"""
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", _mock_fixed_file()):
            result = calculate_transport_fare("飛行機", "A空港", "B空港", "2026-05-01")
        assert result["calculable"] is True
        assert result["fare"] == 15000

    def test_bus_normalized_from_english(self):
        """「bus」が「バス」に正規化されて処理されること"""
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", _mock_fixed_file()):
            result = calculate_transport_fare("bus", "A地点", "B地点", "2026-05-01")
        assert result["calculable"] is True
        assert result["fare"] == 230

    def test_taxi_normalized_from_cab(self):
        """「cab」が「タクシー」に正規化されて処理されること"""
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", _mock_fixed_file()):
            result = calculate_transport_fare("cab", "A地点", "B地点", "2026-05-01")
        assert result["calculable"] is True
        assert result["fare"] == 1500

    def test_airplane_normalized_from_airplane(self):
        """「airplane」が「飛行機」に正規化されて処理されること"""
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", _mock_fixed_file()):
            result = calculate_transport_fare("airplane", "A空港", "B空港", "2026-05-01")
        assert result["calculable"] is True
        assert result["fare"] == 15000

    def test_missing_fixed_fares_file_returns_failure(self):
        """fixed_fares.json が存在しない場合に success=False が返却されること"""
        with patch("os.path.exists", return_value=False):
            result = calculate_transport_fare("バス", "A地点", "B地点", "2026-05-01")
        assert result["success"] is False
        assert result["calculable"] is False


class TestCalculateTransportFareValidation:
    def test_invalid_transport_type_returns_failure(self):
        """不正な交通手段（バイク）で success=False が返却されること"""
        result = calculate_transport_fare("バイク", "渋谷", "品川", "2026-05-01")
        assert result["success"] is False
        assert result["calculable"] is False
        assert isinstance(result["message"], str)

    def test_empty_departure_returns_failure(self):
        """出発地が空文字で success=False が返却されること"""
        result = calculate_transport_fare("電車", "", "品川", "2026-05-01")
        assert result["success"] is False
        assert isinstance(result["message"], str)

    def test_invalid_date_format_returns_failure(self):
        """スラッシュ形式の日付で success=False が返却されること"""
        result = calculate_transport_fare("電車", "渋谷", "品川", "2026/05/01")
        assert result["success"] is False
        assert isinstance(result["message"], str)
