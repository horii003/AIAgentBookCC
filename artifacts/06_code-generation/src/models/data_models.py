from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Normalizers (mode="before" field validators)
# ---------------------------------------------------------------------------

def _normalize_station_name(v: str) -> str:
    for suffix in ("Station", "station", "駅"):
        v = v.removesuffix(suffix)
    return v.strip()


def _normalize_transportation_type(v: str) -> str:
    mapping = {
        "JR": "電車",
        "新幹線": "電車",
        "地下鉄": "電車",
        "モノレール": "電車",
        "ハイヤー": "タクシー",
        "タクシー代": "タクシー",
        "飛機": "飛行機",
        "航空": "飛行機",
        "ANA": "飛行機",
        "JAL": "飛行機",
        "路線バス": "バス",
    }
    return mapping.get(v.strip(), v.strip())


def _strip_and_validate_not_empty(v: str) -> str:
    return v.strip()


# ---------------------------------------------------------------------------
# TransportToolInput
# ---------------------------------------------------------------------------

class TransportToolInput(BaseModel):
    model_config = ConfigDict(strict=False)

    departure: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    transportation_type: Literal["電車", "バス", "タクシー", "飛行機"]
    travel_date: date
    purpose: str = Field(min_length=1)

    @field_validator("departure", "destination", mode="before")
    @classmethod
    def normalize_station_name(cls, v: str) -> str:
        return _normalize_station_name(v)

    @field_validator("transportation_type", mode="before")
    @classmethod
    def normalize_transportation_type(cls, v: str) -> str:
        return _normalize_transportation_type(v)

    @field_validator("purpose", mode="before")
    @classmethod
    def strip_and_validate_not_empty(cls, v: str) -> str:
        return _strip_and_validate_not_empty(v)

    @field_validator("travel_date", mode="before")
    @classmethod
    def validate_not_future(cls, v) -> date:
        if isinstance(v, str):
            try:
                v = date.fromisoformat(v)
            except ValueError:
                raise ValueError("日付はYYYY-MM-DD形式で入力してください")
        if isinstance(v, datetime):
            v = v.date()
        if v > date.today():
            raise ValueError("移動日は本日以前の日付を入力してください")
        return v

    @model_validator(mode="after")
    def check_application_deadline(self) -> TransportToolInput:
        delta = (date.today() - self.travel_date).days
        if delta > 90:
            raise ValueError(
                "申請期限（経費発生日から90日以内）を超過しています。担当部門にご確認ください。"
            )
        return self


# ---------------------------------------------------------------------------
# TrainRoute models
# ---------------------------------------------------------------------------

class TrainRouteEntry(BaseModel):
    departure: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    fare: int = Field(ge=0)


class TrainRouteMaster(BaseModel):
    routes: list[TrainRouteEntry] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# FixedFare models
# ---------------------------------------------------------------------------

class FixedFareEntry(BaseModel):
    transportation_type: Literal["バス", "タクシー", "飛行機"]
    fare: int = Field(ge=0)


class FixedFareMaster(BaseModel):
    entries: list[FixedFareEntry] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Form input models
# ---------------------------------------------------------------------------

class TransportSegment(BaseModel):
    model_config = ConfigDict(strict=False)

    travel_date: date
    departure: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    transportation_type: Literal["電車", "バス", "タクシー", "飛行機"]
    amount: int = Field(ge=0)
    purpose: str = Field(min_length=1)

    @field_validator("travel_date", mode="before")
    @classmethod
    def validate_not_future(cls, v) -> date:
        if isinstance(v, str):
            try:
                v = date.fromisoformat(v)
            except ValueError:
                raise ValueError("日付はYYYY-MM-DD形式で入力してください")
        if isinstance(v, datetime):
            v = v.date()
        if v > date.today():
            raise ValueError("移動日は本日以前の日付を入力してください")
        return v

    @field_validator("departure", "destination", mode="before")
    @classmethod
    def normalize_station_name(cls, v: str) -> str:
        return _normalize_station_name(v)

    @field_validator("transportation_type", mode="before")
    @classmethod
    def normalize_transportation_type(cls, v: str) -> str:
        return _normalize_transportation_type(v)

    @field_validator("purpose", mode="before")
    @classmethod
    def strip_purpose(cls, v: str) -> str:
        return _strip_and_validate_not_empty(v)

    @model_validator(mode="after")
    def check_application_deadline(self) -> "TransportSegment":
        delta = (date.today() - self.travel_date).days
        if delta > 90:
            raise ValueError(
                "申請期限（経費発生日から90日以内）を超過しています。担当部門にご確認ください。"
            )
        return self


class TransportFormInput(BaseModel):
    applicant_name: str = Field(min_length=1)
    application_date: str
    segments: list[TransportSegment] = Field(min_length=1)


class ExpenseItem(BaseModel):
    model_config = ConfigDict(strict=False)

    expense_date: date
    store_name: str = Field(min_length=1)
    amount: int = Field(ge=0)
    item_name: str = Field(min_length=1)
    expense_category: Literal["事務用品費", "宿泊費", "資格精算費", "その他経費"]
    purpose: str = Field(min_length=1)

    @field_validator("expense_date", mode="before")
    @classmethod
    def validate_not_future(cls, v) -> date:
        if isinstance(v, str):
            try:
                v = date.fromisoformat(v)
            except ValueError:
                raise ValueError("日付はYYYY-MM-DD形式で入力してください")
        if isinstance(v, datetime):
            v = v.date()
        if v > date.today():
            raise ValueError("経費発生日は本日以前の日付を入力してください")
        return v

    @field_validator("store_name", "item_name", "purpose", mode="before")
    @classmethod
    def strip_not_empty(cls, v: str) -> str:
        return _strip_and_validate_not_empty(v)

    @model_validator(mode="after")
    def check_application_deadline(self) -> "ExpenseItem":
        delta = (date.today() - self.expense_date).days
        if delta > 90:
            raise ValueError(
                "申請期限（経費発生日から90日以内）を超過しています。担当部門にご確認ください。"
            )
        return self


class ExpenseFormInput(BaseModel):
    applicant_name: str = Field(min_length=1)
    application_date: str
    items: list[ExpenseItem] = Field(min_length=1)


# ---------------------------------------------------------------------------
# InvocationState
# ---------------------------------------------------------------------------

class InvocationState(BaseModel):
    session_id: str
    applicant_name: str
    application_date: str
