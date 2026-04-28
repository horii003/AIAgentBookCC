"""data_models.py の単体テスト"""
import pytest
from datetime import date
from pydantic import ValidationError

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from models.data_models import (
    UserInputText,
    TrainFareRecord,
    TravelExpenseCalculatorInput,
    TravelItem,
    TravelApplicationFormInput,
    ExpenseItem,
    ExpenseApplicationFormInput,
    parse_amount,
    TRANSPORT_TYPE_MAP,
    EXPENSE_CATEGORY_MAP,
)


# ============ UserInputText ============

class TestUserInputText:
    def test_正常_1文字(self):
        m = UserInputText(text="a")
        assert m.text == "a"

    def test_正常_500文字(self):
        m = UserInputText(text="a" * 500)
        assert len(m.text) == 500

    def test_異常_空文字(self):
        with pytest.raises(ValidationError):
            UserInputText(text="")

    def test_異常_501文字(self):
        with pytest.raises(ValidationError):
            UserInputText(text="a" * 501)


# ============ parse_amount ============

class TestParseAmount:
    def test_カンマ円記号付き文字列(self):
        assert parse_amount("1,000円") == 1000

    def test_数字文字列(self):
        assert parse_amount("500") == 500

    def test_int(self):
        assert parse_amount(200) == 200

    def test_float(self):
        assert parse_amount(1500.0) == 1500

    def test_異常_空文字(self):
        with pytest.raises(ValueError):
            parse_amount("")

    def test_異常_非数値文字列(self):
        with pytest.raises(ValueError):
            parse_amount("abc")


# ============ TravelExpenseCalculatorInput ============

class TestTravelExpenseCalculatorInput:
    def test_正常_電車(self):
        m = TravelExpenseCalculatorInput(
            travel_date="2026-04-28",
            departure="渋谷",
            destination="新宿",
            transport_type="電車",
        )
        assert m.travel_date == date(2026, 4, 28)
        assert m.transport_type == "電車"

    def test_正規化_train_to_電車(self):
        m = TravelExpenseCalculatorInput(
            travel_date="2026-04-28",
            departure="渋谷",
            destination="新宿",
            transport_type="train",
        )
        assert m.transport_type == "電車"

    def test_正規化_bus_to_バス(self):
        m = TravelExpenseCalculatorInput(
            travel_date="2026-04-28",
            departure="A",
            destination="B",
            transport_type="bus",
        )
        assert m.transport_type == "バス"

    def test_正規化_taxi_to_タクシー(self):
        m = TravelExpenseCalculatorInput(
            travel_date="2026-04-28",
            departure="A",
            destination="B",
            transport_type="taxi",
        )
        assert m.transport_type == "タクシー"

    def test_正規化_cab_to_タクシー(self):
        m = TravelExpenseCalculatorInput(
            travel_date="2026-04-28",
            departure="A",
            destination="B",
            transport_type="cab",
        )
        assert m.transport_type == "タクシー"

    def test_正規化_airplane_to_飛行機(self):
        m = TravelExpenseCalculatorInput(
            travel_date="2026-04-28",
            departure="A",
            destination="B",
            transport_type="airplane",
        )
        assert m.transport_type == "飛行機"

    def test_正規化_地下鉄_to_電車(self):
        m = TravelExpenseCalculatorInput(
            travel_date="2026-04-28",
            departure="A",
            destination="B",
            transport_type="地下鉄",
        )
        assert m.transport_type == "電車"

    def test_異常_不正交通手段(self):
        with pytest.raises(ValidationError):
            TravelExpenseCalculatorInput(
                travel_date="2026-04-28",
                departure="A",
                destination="B",
                transport_type="自転車",
            )

    def test_異常_departure空文字(self):
        with pytest.raises(ValidationError):
            TravelExpenseCalculatorInput(
                travel_date="2026-04-28",
                departure="",
                destination="B",
                transport_type="電車",
            )

    def test_異常_destination空文字(self):
        with pytest.raises(ValidationError):
            TravelExpenseCalculatorInput(
                travel_date="2026-04-28",
                departure="A",
                destination="",
                transport_type="電車",
            )

    def test_異常_空白のみdeparture(self):
        with pytest.raises(ValidationError):
            TravelExpenseCalculatorInput(
                travel_date="2026-04-28",
                departure="   ",
                destination="B",
                transport_type="電車",
            )

    def test_異常_不正日付形式_数字のみ(self):
        with pytest.raises(ValidationError):
            TravelExpenseCalculatorInput(
                travel_date="20260428",
                departure="A",
                destination="B",
                transport_type="電車",
            )

    def test_異常_空文字日付(self):
        with pytest.raises(ValidationError):
            TravelExpenseCalculatorInput(
                travel_date="",
                departure="A",
                destination="B",
                transport_type="電車",
            )


# ============ TrainFareRecord ============

class TestTrainFareRecord:
    def test_正常_fare_0(self):
        r = TrainFareRecord(departure="A", destination="B", fare=0)
        assert r.fare == 0

    def test_正常_fare_正の整数(self):
        r = TrainFareRecord(departure="渋谷", destination="新宿", fare=200)
        assert r.fare == 200

    def test_異常_fare_負値(self):
        with pytest.raises(ValidationError):
            TrainFareRecord(departure="A", destination="B", fare=-1)

    def test_異常_departure空文字(self):
        with pytest.raises(ValidationError):
            TrainFareRecord(departure="", destination="B", fare=100)

    def test_異常_destination空文字(self):
        with pytest.raises(ValidationError):
            TrainFareRecord(departure="A", destination="", fare=100)


# ============ TravelApplicationFormInput ============

class TestTravelApplicationFormInput:
    def _make_item(self):
        return {
            "travel_date": "2026-04-28",
            "departure": "渋谷",
            "destination": "新宿",
            "transport_type": "電車",
            "amount": 200,
        }

    def test_正常(self):
        m = TravelApplicationFormInput(
            applicant_name="田中太郎",
            application_date="2026-04-28",
            items=[self._make_item()],
            business_purpose="社内会議",
        )
        assert len(m.items) == 1

    def test_異常_items空リスト(self):
        with pytest.raises(ValidationError):
            TravelApplicationFormInput(
                applicant_name="田中太郎",
                application_date="2026-04-28",
                items=[],
                business_purpose="社内会議",
            )

    def test_異常_business_purpose空文字(self):
        with pytest.raises(ValidationError):
            TravelApplicationFormInput(
                applicant_name="田中太郎",
                application_date="2026-04-28",
                items=[self._make_item()],
                business_purpose="",
            )


# ============ ExpenseApplicationFormInput ============

class TestExpenseApplicationFormInput:
    def _make_item(self):
        return {
            "expense_date": "2026-04-28",
            "category": "事務用品費",
            "amount": 1000,
            "purpose": "業務用文房具",
        }

    def test_正常(self):
        m = ExpenseApplicationFormInput(
            applicant_name="田中太郎",
            application_date="2026-04-28",
            items=[self._make_item()],
        )
        assert len(m.items) == 1

    def test_異常_items空リスト(self):
        with pytest.raises(ValidationError):
            ExpenseApplicationFormInput(
                applicant_name="田中太郎",
                application_date="2026-04-28",
                items=[],
            )

    def test_カテゴリ正規化_文房具(self):
        item = ExpenseItem(
            expense_date="2026-04-28",
            category="文房具",
            amount=500,
            purpose="メモ帳",
        )
        assert item.category == "事務用品費"

    def test_カテゴリ正規化_宿泊(self):
        item = ExpenseItem(
            expense_date="2026-04-28",
            category="宿泊",
            amount=10000,
            purpose="出張",
        )
        assert item.category == "宿泊費"
