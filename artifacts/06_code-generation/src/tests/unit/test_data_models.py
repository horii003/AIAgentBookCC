"""data_models.py の単体テスト"""
import pytest
from datetime import date
from pydantic import ValidationError

from models.data_models import (
    normalize_station_name,
    normalize_transport_type,
    validate_date,
    validate_business_purpose,
    validate_amount,
    normalize_expense_category,
    InvocationState,
    TransportCalculatorInput,
    TransportApplicationInput,
    TransportSegment,
    ExpenseItem,
    ExpenseApplicationInput,
)


# ============ normalize_station_name テスト ============

class TestNormalizeStationName:
    def test_removes_eki_suffix(self):
        assert normalize_station_name("渋谷駅") == "渋谷"

    def test_removes_station_suffix(self):
        assert normalize_station_name("Shibuya Station") == "Shibuya"

    def test_strips_whitespace(self):
        assert normalize_station_name("  新宿  ") == "新宿"

    def test_no_suffix(self):
        assert normalize_station_name("品川") == "品川"

    def test_station_suffix_case_insensitive(self):
        assert normalize_station_name("Tokyo station") == "Tokyo"


# ============ normalize_transport_type テスト ============

class TestNormalizeTransportType:
    def test_train_english(self):
        assert normalize_transport_type("train") == "電車"

    def test_railway_japanese(self):
        assert normalize_transport_type("鉄道") == "電車"

    def test_bus_english(self):
        assert normalize_transport_type("bus") == "バス"

    def test_taxi_english(self):
        assert normalize_transport_type("taxi") == "タクシー"

    def test_cab_english(self):
        assert normalize_transport_type("cab") == "タクシー"

    def test_airplane_english(self):
        assert normalize_transport_type("airplane") == "飛行機"

    def test_plane_english(self):
        assert normalize_transport_type("plane") == "飛行機"

    def test_already_normalized(self):
        assert normalize_transport_type("電車") == "電車"
        assert normalize_transport_type("バス") == "バス"
        assert normalize_transport_type("タクシー") == "タクシー"
        assert normalize_transport_type("飛行機") == "飛行機"


# ============ validate_date テスト ============

class TestValidateDate:
    def test_valid_date_string(self):
        result = validate_date("2026-05-01")
        assert result == date(2026, 5, 1)

    def test_date_object_passthrough(self):
        d = date(2026, 5, 1)
        assert validate_date(d) == d

    def test_invalid_format_slash(self):
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            validate_date("2026/05/01")

    def test_invalid_format_string(self):
        with pytest.raises(ValueError):
            validate_date("invalid")


# ============ validate_business_purpose テスト ============

class TestValidateBusinessPurpose:
    def test_valid_purpose(self):
        assert validate_business_purpose("顧客訪問") == "顧客訪問"

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            validate_business_purpose("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError):
            validate_business_purpose("   ")


# ============ validate_amount テスト ============

class TestValidateAmount:
    def test_valid_amount(self):
        assert validate_amount(100) == 100

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            validate_amount(0)

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            validate_amount(-1)


# ============ normalize_expense_category テスト ============

class TestNormalizeExpenseCategory:
    def test_office_supplies(self):
        assert normalize_expense_category("事務用品") == "事務用品費"

    def test_stationery(self):
        assert normalize_expense_category("文房具") == "事務用品費"

    def test_accommodation(self):
        assert normalize_expense_category("宿泊") == "宿泊費"

    def test_qualification(self):
        assert normalize_expense_category("資格") == "資格取得費"

    def test_others(self):
        assert normalize_expense_category("その他") == "その他経費"

    def test_unknown_becomes_other(self):
        assert normalize_expense_category("謎の経費") == "その他経費"

    def test_already_normalized(self):
        assert normalize_expense_category("事務用品費") == "事務用品費"


# ============ TransportCalculatorInput テスト ============

class TestTransportCalculatorInput:
    def test_valid_input(self):
        data = TransportCalculatorInput(
            transport_type="電車",
            departure="渋谷",
            destination="品川",
            travel_date="2026-05-01",
        )
        assert data.transport_type == "電車"
        assert data.departure == "渋谷"
        assert data.travel_date == date(2026, 5, 1)

    def test_normalizes_station_name(self):
        data = TransportCalculatorInput(
            transport_type="電車",
            departure="渋谷駅",
            destination="品川駅",
            travel_date="2026-05-01",
        )
        assert data.departure == "渋谷"
        assert data.destination == "品川"

    def test_normalizes_transport_type(self):
        data = TransportCalculatorInput(
            transport_type="train",
            departure="渋谷",
            destination="品川",
            travel_date="2026-05-01",
        )
        assert data.transport_type == "電車"

    def test_empty_departure_raises(self):
        with pytest.raises(ValidationError):
            TransportCalculatorInput(
                transport_type="電車",
                departure="",
                destination="品川",
                travel_date="2026-05-01",
            )

    def test_invalid_transport_type_raises(self):
        with pytest.raises(ValidationError):
            TransportCalculatorInput(
                transport_type="自転車",
                departure="渋谷",
                destination="品川",
                travel_date="2026-05-01",
            )

    def test_invalid_date_raises(self):
        with pytest.raises(ValidationError):
            TransportCalculatorInput(
                transport_type="電車",
                departure="渋谷",
                destination="品川",
                travel_date="2026/05/01",
            )


# ============ TransportApplicationInput テスト ============

class TestTransportApplicationInput:
    def test_valid_input(self):
        data = TransportApplicationInput(
            business_purpose="顧客訪問",
            segments=[
                {
                    "travel_date": "2026-05-01",
                    "departure": "渋谷",
                    "destination": "品川",
                    "transport_type": "電車",
                    "fare": 250,
                    "business_purpose": "顧客訪問",
                }
            ],
        )
        assert len(data.segments) == 1

    def test_empty_segments_raises(self):
        with pytest.raises(ValidationError):
            TransportApplicationInput(
                business_purpose="顧客訪問",
                segments=[],
            )


# ============ ExpenseApplicationInput テスト ============

class TestExpenseApplicationInput:
    def test_valid_input(self):
        data = ExpenseApplicationInput(
            business_purpose="事務用品購入",
            expense_items=[
                {
                    "purchase_date": "2026-05-01",
                    "store_name": "文房具店",
                    "item_name": "ボールペン",
                    "amount": 200,
                    "expense_category": "事務用品費",
                }
            ],
        )
        assert len(data.expense_items) == 1

    def test_empty_items_raises(self):
        with pytest.raises(ValidationError):
            ExpenseApplicationInput(
                business_purpose="事務用品購入",
                expense_items=[],
            )
