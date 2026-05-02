import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from models.data_models import (
    ExpenseFormInput,
    ExpenseItem,
    FixedFareEntry,
    FixedFareMaster,
    InvocationState,
    TrainRouteEntry,
    TrainRouteMaster,
    TransportFormInput,
    TransportSegment,
    TransportToolInput,
)


def _today_minus(days: int) -> str:
    return (date.today() - timedelta(days=days)).isoformat()


def _today_plus(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


# ---------------------------------------------------------------------------
# TransportToolInput
# ---------------------------------------------------------------------------

class TestTransportToolInput:
    def test_valid_input(self):
        inp = TransportToolInput(
            departure="渋谷",
            destination="新宿",
            transportation_type="電車",
            travel_date=_today_minus(1),
            purpose="営業訪問",
        )
        assert inp.departure == "渋谷"
        assert inp.transportation_type == "電車"

    def test_station_name_normalization(self):
        inp = TransportToolInput(
            departure="渋谷駅",
            destination="Shibuya Station",
            transportation_type="電車",
            travel_date=_today_minus(1),
            purpose="会議",
        )
        assert inp.departure == "渋谷"
        assert inp.destination == "Shibuya"

    def test_transportation_type_normalization_jr(self):
        inp = TransportToolInput(
            departure="渋谷",
            destination="新宿",
            transportation_type="JR",
            travel_date=_today_minus(1),
            purpose="会議",
        )
        assert inp.transportation_type == "電車"

    def test_transportation_type_normalization_shinkansen(self):
        inp = TransportToolInput(
            departure="東京",
            destination="大阪",
            transportation_type="新幹線",
            travel_date=_today_minus(1),
            purpose="出張",
        )
        assert inp.transportation_type == "電車"

    def test_transportation_type_normalization_hire(self):
        inp = TransportToolInput(
            departure="渋谷",
            destination="品川",
            transportation_type="ハイヤー",
            travel_date=_today_minus(1),
            purpose="接待",
        )
        assert inp.transportation_type == "タクシー"

    def test_transportation_type_normalization_ana(self):
        inp = TransportToolInput(
            departure="東京",
            destination="札幌",
            transportation_type="ANA",
            travel_date=_today_minus(1),
            purpose="出張",
        )
        assert inp.transportation_type == "飛行機"

    def test_transportation_type_normalization_local_bus(self):
        inp = TransportToolInput(
            departure="渋谷",
            destination="恵比寿",
            transportation_type="路線バス",
            travel_date=_today_minus(1),
            purpose="移動",
        )
        assert inp.transportation_type == "バス"

    def test_future_date_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            TransportToolInput(
                departure="渋谷",
                destination="新宿",
                transportation_type="電車",
                travel_date=_today_plus(1),
                purpose="会議",
            )
        assert "本日以前" in str(exc_info.value)

    def test_91days_ago_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            TransportToolInput(
                departure="渋谷",
                destination="新宿",
                transportation_type="電車",
                travel_date=_today_minus(91),
                purpose="会議",
            )
        assert "90日" in str(exc_info.value)

    def test_90days_ago_ok(self):
        inp = TransportToolInput(
            departure="渋谷",
            destination="新宿",
            transportation_type="電車",
            travel_date=_today_minus(90),
            purpose="会議",
        )
        assert inp is not None

    def test_empty_purpose_raises(self):
        with pytest.raises(ValidationError):
            TransportToolInput(
                departure="渋谷",
                destination="新宿",
                transportation_type="電車",
                travel_date=_today_minus(1),
                purpose="",
            )

    def test_whitespace_only_purpose_raises(self):
        with pytest.raises(ValidationError):
            TransportToolInput(
                departure="渋谷",
                destination="新宿",
                transportation_type="電車",
                travel_date=_today_minus(1),
                purpose="   ",
            )

    def test_invalid_transportation_type_raises(self):
        with pytest.raises(ValidationError):
            TransportToolInput(
                departure="渋谷",
                destination="新宿",
                transportation_type="自動車",
                travel_date=_today_minus(1),
                purpose="会議",
            )


# ---------------------------------------------------------------------------
# TrainRouteEntry / TrainRouteMaster
# ---------------------------------------------------------------------------

class TestTrainRouteModels:
    def test_valid_entry(self):
        entry = TrainRouteEntry(departure="渋谷", destination="新宿", fare=200)
        assert entry.fare == 200

    def test_negative_fare_raises(self):
        with pytest.raises(ValidationError):
            TrainRouteEntry(departure="渋谷", destination="新宿", fare=-1)

    def test_master_empty_routes_ok(self):
        master = TrainRouteMaster(routes=[])
        assert master.routes == []


# ---------------------------------------------------------------------------
# FixedFareEntry / FixedFareMaster
# ---------------------------------------------------------------------------

class TestFixedFareModels:
    def test_valid_entry(self):
        entry = FixedFareEntry(transportation_type="バス", fare=230)
        assert entry.fare == 230

    def test_invalid_type_raises(self):
        with pytest.raises(ValidationError):
            FixedFareEntry(transportation_type="電車", fare=200)

    def test_negative_fare_raises(self):
        with pytest.raises(ValidationError):
            FixedFareEntry(transportation_type="タクシー", fare=-1)

    def test_master_entries_ok(self):
        master = FixedFareMaster(entries=[
            FixedFareEntry(transportation_type="バス", fare=230),
            FixedFareEntry(transportation_type="タクシー", fare=730),
        ])
        assert len(master.entries) == 2


# ---------------------------------------------------------------------------
# Form input models
# ---------------------------------------------------------------------------

class TestTransportFormInput:
    def test_valid(self):
        seg = TransportSegment(
            travel_date="2026-04-28",
            departure="渋谷",
            destination="新宿",
            transportation_type="電車",
            amount=200,
            purpose="会議",
        )
        form = TransportFormInput(
            applicant_name="田中太郎",
            application_date="2026-05-02",
            segments=[seg],
        )
        assert len(form.segments) == 1

    def test_negative_amount_raises(self):
        with pytest.raises(ValidationError):
            TransportSegment(
                travel_date="2026-04-28",
                departure="渋谷",
                destination="新宿",
                transportation_type="電車",
                amount=-1,
                purpose="会議",
            )


class TestExpenseFormInput:
    def test_valid(self):
        item = ExpenseItem(
            expense_date="2026-04-28",
            store_name="コンビニA",
            amount=500,
            item_name="ボールペン",
            expense_category="事務用品費",
            purpose="業務使用",
        )
        form = ExpenseFormInput(
            applicant_name="田中太郎",
            application_date="2026-05-02",
            items=[item],
        )
        assert len(form.items) == 1

    def test_invalid_category_raises(self):
        with pytest.raises(ValidationError):
            ExpenseItem(
                expense_date="2026-04-28",
                store_name="コンビニ",
                amount=500,
                item_name="ペン",
                expense_category="交際費",
                purpose="業務",
            )


# ---------------------------------------------------------------------------
# InvocationState
# ---------------------------------------------------------------------------

class TestInvocationState:
    def test_valid(self):
        state = InvocationState(
            session_id="20260502_143022_a1b2c3d4",
            applicant_name="田中太郎",
            application_date="2026-05-02",
        )
        assert state.session_id == "20260502_143022_a1b2c3d4"
