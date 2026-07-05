"""transport_toolsの単体テスト"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import pytest
from unittest.mock import patch, mock_open
import tools.transport_tools as tt
from tools.transport_tools import calculate_transport_fare


def _reset_cache():
    tt._train_fares_cache = None
    tt._fixed_fares_cache = None


TRAIN_FARES = json.dumps({
    "渋谷": {"新宿": 200, "品川": 180},
    "新宿": {"渋谷": 200, "東京": 210},
})
FIXED_FARES = json.dumps({
    "バス": 230,
    "タクシー": 10000,
    "飛行機": 50000,
})


def _setup_cache():
    tt._train_fares_cache = json.loads(TRAIN_FARES)
    tt._fixed_fares_cache = json.loads(FIXED_FARES)


class TestLoadFareData:
    def setup_method(self):
        _reset_cache()

    def test_ファイル存在しない場合Falseを返す(self, tmp_path):
        with patch("tools.transport_tools.os.path.exists", return_value=False):
            ok, msg = tt._load_fare_data()
        assert ok is False
        assert "見つかりません" in msg

    def test_JSONDecodeErrorでFalseを返す(self):
        with patch("tools.transport_tools.os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="invalid json")):
                ok, msg = tt._load_fare_data()
        assert ok is False
        assert "形式が不正" in msg

    def test_成功時にTrueを返す(self):
        _setup_cache()
        ok, msg = tt._load_fare_data()
        assert ok is True
        assert msg == ""


class TestSearchTrainFare:
    def setup_method(self):
        _setup_cache()

    def test_電車運賃を取得できる(self):
        result = tt._search_train_fare("渋谷", "新宿")
        assert result["fare"] == 200
        assert "渋谷" in result["calculation_basis"]

    def test_経路未登録でFalseを返す(self):
        result = tt._search_train_fare("渋谷", "大阪")
        assert result["success"] is False
        assert "経路が見つかりません" in result["message"]


class TestGetFixedFare:
    def setup_method(self):
        _setup_cache()

    def test_バスの固定運賃を取得できる(self):
        result = tt._get_fixed_fare("バス")
        assert result["fare"] == 230

    def test_タクシーの固定運賃を取得できる(self):
        result = tt._get_fixed_fare("タクシー")
        assert result["fare"] == 10000

    def test_未登録交通手段でFalseを返す(self):
        result = tt._get_fixed_fare("ロケット")
        assert result["success"] is False


class TestCalculateTransportFare:
    def setup_method(self):
        _setup_cache()

    def test_電車運賃の計算(self):
        result = calculate_transport_fare(
            departure="渋谷",
            destination="新宿",
            transport_type="電車",
            travel_date="2026-07-03",
            purpose="取引先訪問",
        )
        assert result["fare"] == 200
        assert result["transport_type"] == "電車"

    def test_駅サフィックスが除去される(self):
        result = calculate_transport_fare(
            departure="渋谷駅",
            destination="新宿駅",
            transport_type="電車",
            travel_date="2026-07-03",
            purpose="取引先訪問",
        )
        assert result["departure"] == "渋谷"
        assert result["destination"] == "新宿"

    def test_バスの固定運賃計算(self):
        result = calculate_transport_fare(
            departure="会社前",
            destination="駅前",
            transport_type="バス",
            travel_date="2026-07-03",
            purpose="出張",
        )
        assert result["fare"] == 230

    def test_英語表記のtransport_typeが変換される(self):
        result = calculate_transport_fare(
            departure="渋谷",
            destination="新宿",
            transport_type="train",
            travel_date="2026-07-03",
            purpose="出張",
        )
        assert result["transport_type"] == "電車"
        assert result["fare"] == 200

    def test_バリデーションエラーでFalseを返す(self):
        result = calculate_transport_fare(
            departure="",
            destination="新宿",
            transport_type="電車",
            travel_date="2026-07-03",
            purpose="取引先訪問",
        )
        assert result["success"] is False

    def test_不正な交通手段でFalseを返す(self):
        result = calculate_transport_fare(
            departure="渋谷",
            destination="新宿",
            transport_type="自転車",
            travel_date="2026-07-03",
            purpose="取引先訪問",
        )
        assert result["success"] is False
