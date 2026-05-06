# 参照: DD-01a 交通費計算ツール詳細設計書, DD-01b 申請書生成ツール詳細設計書, BD-02 データモデル基本設計書
"""models/data_models.py の単体テスト"""
import sys
import os
from datetime import date, timedelta

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from models.data_models import (
    normalize_station_name,
    normalize_transport_type,
    normalize_expense_category,
    parse_date_field,
    validate_positive_amount,
    validate_required_string,
    RailwayRouteMaster,
    FareCalculationInput,
    TransportSegment,
    TransportApplicationData,
    ExpenseApplicationData,
)


class TestNormalizeStationName:
    """normalize_station_name のテスト"""

    def test_removes_eki_suffix(self):
        assert normalize_station_name("渋谷駅") == "渋谷"

    def test_removes_ekimae_suffix(self):
        assert normalize_station_name("渋谷駅前") == "渋谷"

    def test_no_suffix(self):
        assert normalize_station_name("渋谷") == "渋谷"

    def test_shinjuku_eki(self):
        assert normalize_station_name("新宿駅") == "新宿"

    def test_strips_whitespace(self):
        assert normalize_station_name("  東京駅  ") == "東京"


class TestNormalizeTransportType:
    """normalize_transport_type のテスト"""

    def test_densha(self):
        assert normalize_transport_type("電車") == "電車"

    def test_tetsudo(self):
        assert normalize_transport_type("鉄道") == "電車"

    def test_jr(self):
        assert normalize_transport_type("JR") == "電車"

    def test_chikatetsu(self):
        assert normalize_transport_type("地下鉄") == "電車"

    def test_dentetsu(self):
        assert normalize_transport_type("電鉄") == "電車"

    def test_bus(self):
        assert normalize_transport_type("バス") == "バス"

    def test_rosen_bus(self):
        assert normalize_transport_type("路線バス") == "バス"

    def test_taxi(self):
        assert normalize_transport_type("タクシー") == "タクシー"

    def test_taxi_english(self):
        assert normalize_transport_type("taxi") == "タクシー"

    def test_hikouki(self):
        assert normalize_transport_type("飛行機") == "飛行機"

    def test_kokuki(self):
        assert normalize_transport_type("航空機") == "飛行機"

    def test_airplane_english(self):
        assert normalize_transport_type("airplane") == "飛行機"

    def test_invalid_shinkansen(self):
        with pytest.raises(ValueError, match="交通手段のエラー"):
            normalize_transport_type("新幹線")

    def test_invalid_unknown(self):
        with pytest.raises(ValueError, match="交通手段のエラー"):
            normalize_transport_type("船")


class TestNormalizeExpenseCategory:
    """normalize_expense_category のテスト"""

    def test_jimu_yohin(self):
        assert normalize_expense_category("事務用品") == "事務用品費"

    def test_jimu_yohin_full(self):
        assert normalize_expense_category("事務用品費") == "事務用品費"

    def test_shukuhaku(self):
        assert normalize_expense_category("宿泊") == "宿泊費"

    def test_shukuhaku_full(self):
        assert normalize_expense_category("宿泊費") == "宿泊費"

    def test_shikaku_hi(self):
        assert normalize_expense_category("資格費") == "資格精算費"

    def test_shikaku(self):
        assert normalize_expense_category("資格") == "資格精算費"

    def test_shikaku_full(self):
        assert normalize_expense_category("資格精算費") == "資格精算費"

    def test_sonota(self):
        assert normalize_expense_category("その他経費") == "その他経費"

    def test_unknown_becomes_sonota(self):
        # BRL-17: 判断不可時は「その他経費」として扱う（エラーにしない）
        assert normalize_expense_category("新幹線代") == "その他経費"

    def test_unknown_meal(self):
        assert normalize_expense_category("会食費") == "その他経費"


class TestParseDateField:
    """parse_date_field のテスト"""

    def test_iso_format(self):
        result = parse_date_field("2026-05-06")
        assert result == date(2026, 5, 6)

    def test_slash_format(self):
        result = parse_date_field("2026/05/06")
        assert result is not None

    def test_none_returns_none(self):
        assert parse_date_field(None) is None

    def test_date_object_passthrough(self):
        d = date(2026, 5, 6)
        assert parse_date_field(d) == d

    def test_invalid_string_raises(self):
        with pytest.raises(ValueError, match="日付のエラー"):
            parse_date_field("abc")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="日付のエラー"):
            parse_date_field("")


class TestValidatePositiveAmount:
    """validate_positive_amount のテスト"""

    def test_positive_amount(self):
        assert validate_positive_amount(100) == 100

    def test_minimum_amount(self):
        assert validate_positive_amount(1) == 1

    def test_zero_raises(self):
        with pytest.raises(ValueError, match="金額のエラー"):
            validate_positive_amount(0)

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="金額のエラー"):
            validate_positive_amount(-100)


class TestValidateRequiredString:
    """validate_required_string のテスト"""

    def test_normal_string(self):
        assert validate_required_string("渋谷") == "渋谷"

    def test_strips_whitespace(self):
        assert validate_required_string("  渋谷  ") == "渋谷"

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="入力のエラー"):
            validate_required_string("")

    def test_none_raises(self):
        with pytest.raises(ValueError, match="入力のエラー"):
            validate_required_string(None)

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="入力のエラー"):
            validate_required_string("   ")

    def test_500_chars_passes(self):
        # 境界値: 500文字はOK
        long_str = "あ" * 500
        result = validate_required_string(long_str)
        assert len(result) == 500

    def test_501_chars_raises(self):
        # 境界値: 501文字はNG
        long_str = "あ" * 501
        with pytest.raises(ValueError, match="入力のエラー"):
            validate_required_string(long_str)


class TestFareCalculationInput:
    """FareCalculationInput のテスト"""

    def test_valid_input(self):
        data = FareCalculationInput(
            departure="渋谷",
            destination="新宿",
            transport_type="電車",
        )
        assert data.departure == "渋谷"
        assert data.destination == "新宿"
        assert data.transport_type == "電車"
        assert data.travel_date is None

    def test_station_name_normalized(self):
        # BRL-15: 駅名正規化
        data = FareCalculationInput(
            departure="渋谷駅",
            destination="新宿駅前",
            transport_type="電車",
        )
        assert data.departure == "渋谷"
        assert data.destination == "新宿"

    def test_transport_type_normalized(self):
        # BRL-14: 交通手段正規化
        data = FareCalculationInput(
            departure="渋谷",
            destination="新宿",
            transport_type="JR",
        )
        assert data.transport_type == "電車"

    def test_travel_date_none_passes(self):
        # travel_dateはNoneでも通過すること
        data = FareCalculationInput(
            departure="渋谷",
            destination="新宿",
            transport_type="電車",
            travel_date=None,
        )
        assert data.travel_date is None

    def test_travel_date_string_converted(self):
        data = FareCalculationInput(
            departure="渋谷",
            destination="新宿",
            transport_type="電車",
            travel_date="2026-05-06",
        )
        assert data.travel_date == date(2026, 5, 6)

    def test_departure_empty_raises(self):
        with pytest.raises(ValidationError):
            FareCalculationInput(
                departure="",
                destination="新宿",
                transport_type="電車",
            )

    def test_destination_empty_raises(self):
        with pytest.raises(ValidationError):
            FareCalculationInput(
                departure="渋谷",
                destination="",
                transport_type="電車",
            )

    def test_invalid_transport_raises(self):
        with pytest.raises(ValidationError):
            FareCalculationInput(
                departure="渋谷",
                destination="新宿",
                transport_type="新幹線",
            )

    def test_departure_500_chars_passes(self):
        # 境界値: 500文字はOK
        long_name = "あ" * 500
        data = FareCalculationInput(
            departure=long_name,
            destination="新宿",
            transport_type="電車",
        )
        assert len(data.departure) == 500

    def test_departure_501_chars_raises(self):
        # 境界値: 501文字はNG
        long_name = "あ" * 501
        with pytest.raises(ValidationError):
            FareCalculationInput(
                departure=long_name,
                destination="新宿",
                transport_type="電車",
            )


class TestTransportSegment:
    """TransportSegment のテスト"""

    def test_valid_segment(self):
        seg = TransportSegment(
            travel_date="2026-05-06",
            departure="渋谷",
            destination="新宿",
            transport_type="電車",
            fare=200,
        )
        assert seg.fare == 200
        assert seg.travel_date == date(2026, 5, 6)

    def test_fare_zero_raises(self):
        with pytest.raises(ValidationError):
            TransportSegment(
                travel_date="2026-05-06",
                departure="渋谷",
                destination="新宿",
                transport_type="電車",
                fare=0,
            )

    def test_fare_1_passes(self):
        # 最小値1円でOK
        seg = TransportSegment(
            travel_date="2026-05-06",
            departure="渋谷",
            destination="新宿",
            transport_type="電車",
            fare=1,
        )
        assert seg.fare == 1

    def test_fare_negative_raises(self):
        with pytest.raises(ValidationError):
            TransportSegment(
                travel_date="2026-05-06",
                departure="渋谷",
                destination="新宿",
                transport_type="電車",
                fare=-100,
            )


class TestTransportApplicationData:
    """TransportApplicationData のテスト"""

    def test_valid_data(self):
        data = TransportApplicationData(
            applicant_name="山田太郎",
            application_date="2026-05-06",
            segments=[
                {
                    "travel_date": "2026-05-01",
                    "departure": "渋谷",
                    "destination": "新宿",
                    "transport_type": "電車",
                    "fare": 200,
                }
            ],
            purpose="取引先訪問",
        )
        assert data.applicant_name == "山田太郎"
        assert len(data.segments) == 1

    def test_empty_segments_raises(self):
        with pytest.raises(ValidationError):
            TransportApplicationData(
                applicant_name="山田太郎",
                application_date="2026-05-06",
                segments=[],
                purpose="取引先訪問",
            )

    def test_empty_applicant_name_raises(self):
        with pytest.raises(ValidationError):
            TransportApplicationData(
                applicant_name="",
                application_date="2026-05-06",
                segments=[
                    {
                        "travel_date": "2026-05-01",
                        "departure": "渋谷",
                        "destination": "新宿",
                        "transport_type": "電車",
                        "fare": 200,
                    }
                ],
                purpose="取引先訪問",
            )


class TestExpenseApplicationData:
    """ExpenseApplicationData のテスト"""

    def test_valid_data(self):
        data = ExpenseApplicationData(
            applicant_name="山田太郎",
            application_date="2026-05-06",
            store_name="文具屋",
            expense_category="事務用品費",
            amount=1000,
            expense_date="2026-04-01",
            purpose="業務用品購入",
        )
        assert data.applicant_name == "山田太郎"
        assert data.expense_category == "事務用品費"

    def test_90_days_difference_passes(self):
        # BRL-12: 90日差はOK
        app_date = date(2026, 5, 6)
        exp_date = app_date - timedelta(days=90)
        data = ExpenseApplicationData(
            applicant_name="山田太郎",
            application_date=app_date.isoformat(),
            store_name="文具屋",
            expense_category="事務用品費",
            amount=1000,
            expense_date=exp_date.isoformat(),
            purpose="業務用品購入",
        )
        assert data is not None

    def test_91_days_difference_raises(self):
        # BRL-12: 91日差はNG
        app_date = date(2026, 5, 6)
        exp_date = app_date - timedelta(days=91)
        with pytest.raises(ValidationError, match="申請のエラー"):
            ExpenseApplicationData(
                applicant_name="山田太郎",
                application_date=app_date.isoformat(),
                store_name="文具屋",
                expense_category="事務用品費",
                amount=1000,
                expense_date=exp_date.isoformat(),
                purpose="業務用品購入",
            )

    def test_same_day_passes(self):
        # BRL-12: 0日差（同日）はOK
        today = date(2026, 5, 6)
        data = ExpenseApplicationData(
            applicant_name="山田太郎",
            application_date=today.isoformat(),
            store_name="文具屋",
            expense_category="事務用品費",
            amount=1000,
            expense_date=today.isoformat(),
            purpose="業務用品購入",
        )
        assert data is not None

    def test_amount_zero_raises(self):
        with pytest.raises(ValidationError):
            ExpenseApplicationData(
                applicant_name="山田太郎",
                application_date="2026-05-06",
                store_name="文具屋",
                expense_category="事務用品費",
                amount=0,
                expense_date="2026-04-01",
                purpose="業務用品購入",
            )

    def test_amount_1_passes(self):
        # 最小値1円でOK
        data = ExpenseApplicationData(
            applicant_name="山田太郎",
            application_date="2026-05-06",
            store_name="文具屋",
            expense_category="事務用品費",
            amount=1,
            expense_date="2026-04-01",
            purpose="業務用品購入",
        )
        assert data.amount == 1

    def test_expense_category_normalized(self):
        # BRL-17: 経費区分の正規化（「事務用品」→「事務用品費」）
        data = ExpenseApplicationData(
            applicant_name="山田太郎",
            application_date="2026-05-06",
            store_name="文具屋",
            expense_category="事務用品",
            amount=1000,
            expense_date="2026-04-01",
            purpose="業務用品購入",
        )
        assert data.expense_category == "事務用品費"

    def test_unknown_category_becomes_sonota(self):
        # BRL-17: 判断不可は「その他経費」に変換（エラーにしない）
        data = ExpenseApplicationData(
            applicant_name="山田太郎",
            application_date="2026-05-06",
            store_name="レストラン",
            expense_category="新幹線代",
            amount=1000,
            expense_date="2026-04-01",
            purpose="会食",
        )
        assert data.expense_category == "その他経費"

    def test_empty_store_name_raises(self):
        with pytest.raises(ValidationError):
            ExpenseApplicationData(
                applicant_name="山田太郎",
                application_date="2026-05-06",
                store_name="",
                expense_category="事務用品費",
                amount=1000,
                expense_date="2026-04-01",
                purpose="業務用品購入",
            )
