"""Unit tests for models/data_models.py"""
import pytest
from datetime import date
from pydantic import ValidationError

from models.data_models import (
    UserInputText,
    TransportExpenseCalculatorInput,
    TrainFareRecord,
    TransportApplicationFormInput,
    TransportItem,
    ExpenseApplicationFormInput,
    ExpenseItem,
    parse_amount,
    parse_date,
    normalize_transport_type,
    TRANSPORT_TYPE_MAP,
    EXPENSE_CATEGORY_MAP,
)


# ---- UserInputText ----

class TestUserInputText:
    def test_valid_single_char(self):
        m = UserInputText(text="a")
        assert m.text == "a"

    def test_valid_500_chars(self):
        m = UserInputText(text="x" * 500)
        assert len(m.text) == 500

    def test_empty_string_raises(self):
        with pytest.raises(ValidationError):
            UserInputText(text="")

    def test_501_chars_raises(self):
        with pytest.raises(ValidationError):
            UserInputText(text="x" * 501)


# ---- parse_date ----

class TestParseDate:
    def test_valid_date_string(self):
        result = parse_date("2026-04-28")
        assert result == date(2026, 4, 28)

    def test_date_object_passthrough(self):
        d = date(2026, 1, 1)
        assert parse_date(d) == d

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            parse_date("28/04/2026")

    def test_invalid_string_raises(self):
        with pytest.raises(ValueError):
            parse_date("not-a-date")


# ---- normalize_transport_type ----

class TestNormalizeTransportType:
    def test_train_to_densha(self):
        assert normalize_transport_type("train") == "電車"

    def test_bus(self):
        assert normalize_transport_type("bus") == "バス"

    def test_taxi(self):
        assert normalize_transport_type("taxi") == "タクシー"

    def test_cab_to_taxi(self):
        assert normalize_transport_type("cab") == "タクシー"

    def test_airplane(self):
        assert normalize_transport_type("airplane") == "飛行機"

    def test_plane_to_hikouki(self):
        assert normalize_transport_type("plane") == "飛行機"

    def test_chikatetsu_to_densha(self):
        assert normalize_transport_type("地下鉄") == "電車"

    def test_tetsudo_to_densha(self):
        assert normalize_transport_type("鉄道") == "電車"

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            normalize_transport_type("自転車")


# ---- TransportExpenseCalculatorInput ----

class TestTransportExpenseCalculatorInput:
    def test_valid_input(self):
        m = TransportExpenseCalculatorInput(
            transport_date="2026-04-28",
            departure="東京",
            destination="大阪",
            transport_type="電車",
        )
        assert m.transport_date == date(2026, 4, 28)
        assert m.transport_type == "電車"

    def test_date_conversion(self):
        m = TransportExpenseCalculatorInput(
            transport_date="2026-01-15",
            departure="A",
            destination="B",
            transport_type="バス",
        )
        assert m.transport_date == date(2026, 1, 15)

    def test_invalid_date_raises(self):
        with pytest.raises(ValidationError):
            TransportExpenseCalculatorInput(
                transport_date="invalid-date",
                departure="A",
                destination="B",
                transport_type="電車",
            )

    def test_transport_type_normalization(self):
        m = TransportExpenseCalculatorInput(
            transport_date="2026-04-28",
            departure="A",
            destination="B",
            transport_type="train",
        )
        assert m.transport_type == "電車"

    def test_invalid_transport_type_raises(self):
        with pytest.raises(ValidationError):
            TransportExpenseCalculatorInput(
                transport_date="2026-04-28",
                departure="A",
                destination="B",
                transport_type="自転車",
            )

    def test_empty_departure_raises(self):
        with pytest.raises(ValidationError):
            TransportExpenseCalculatorInput(
                transport_date="2026-04-28",
                departure="",
                destination="B",
                transport_type="電車",
            )

    def test_empty_destination_raises(self):
        with pytest.raises(ValidationError):
            TransportExpenseCalculatorInput(
                transport_date="2026-04-28",
                departure="A",
                destination="",
                transport_type="電車",
            )

    def test_whitespace_only_departure_raises(self):
        with pytest.raises(ValidationError):
            TransportExpenseCalculatorInput(
                transport_date="2026-04-28",
                departure="   ",
                destination="B",
                transport_type="電車",
            )

    def test_whitespace_only_destination_raises(self):
        with pytest.raises(ValidationError):
            TransportExpenseCalculatorInput(
                transport_date="2026-04-28",
                departure="A",
                destination="   ",
                transport_type="電車",
            )


# ---- TrainFareRecord ----

class TestTrainFareRecord:
    def test_fare_zero_valid(self):
        r = TrainFareRecord(departure="A", destination="B", fare=0)
        assert r.fare == 0

    def test_fare_negative_raises(self):
        with pytest.raises(ValidationError):
            TrainFareRecord(departure="A", destination="B", fare=-1)

    def test_empty_departure_raises(self):
        with pytest.raises(ValidationError):
            TrainFareRecord(departure="", destination="B", fare=100)

    def test_empty_destination_raises(self):
        with pytest.raises(ValidationError):
            TrainFareRecord(departure="A", destination="", fare=100)

    def test_fare_string_conversion(self):
        r = TrainFareRecord(departure="A", destination="B", fare="500")
        assert r.fare == 500


# ---- TransportApplicationFormInput ----

class TestTransportApplicationFormInput:
    def _make_item(self, no=1):
        return {
            "no": no,
            "transport_date": "2026-04-28",
            "departure": "東京",
            "destination": "大阪",
            "transport_type": "電車",
            "amount": 1000,
            "business_purpose": "出張",
        }

    def test_valid_input(self):
        m = TransportApplicationFormInput(
            applicant_name="山田太郎",
            application_date="2026-04-28",
            items=[self._make_item()],
            business_purpose="出張",
        )
        assert m.applicant_name == "山田太郎"
        assert len(m.items) == 1

    def test_empty_items_raises(self):
        with pytest.raises(ValidationError):
            TransportApplicationFormInput(
                applicant_name="山田太郎",
                application_date="2026-04-28",
                items=[],
                business_purpose="出張",
            )


# ---- ExpenseApplicationFormInput ----

class TestExpenseApplicationFormInput:
    def _make_item(self, no=1):
        return {
            "no": no,
            "purchase_date": "2026-04-28",
            "store_name": "文具屋",
            "item_name": "ボールペン",
            "expense_category": "事務用品費",
            "amount": 500,
            "business_purpose": "業務用",
        }

    def test_valid_input(self):
        m = ExpenseApplicationFormInput(
            applicant_name="田中花子",
            application_date="2026-04-28",
            items=[self._make_item()],
            business_purpose="業務用品購入",
        )
        assert m.applicant_name == "田中花子"
        assert len(m.items) == 1

    def test_empty_items_raises(self):
        with pytest.raises(ValidationError):
            ExpenseApplicationFormInput(
                applicant_name="田中花子",
                application_date="2026-04-28",
                items=[],
                business_purpose="業務用品購入",
            )


# ---- parse_amount ----

class TestParseAmount:
    def test_comma_yen_string(self):
        assert parse_amount("1,000円") == 1000

    def test_plain_string(self):
        assert parse_amount("500") == 500

    def test_no_comma_integer_string(self):
        assert parse_amount("1200") == 1200

    def test_int_passthrough(self):
        assert parse_amount(500) == 500

    def test_float_truncation(self):
        assert parse_amount(500.9) == 500
