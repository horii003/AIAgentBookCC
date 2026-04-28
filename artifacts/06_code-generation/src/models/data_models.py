"""データモデルの定義

業務ドメインに応じたPydanticモデルを定義する。
各モデルはツール入力、エージェント状態、マスタデータの型安全性を保証する。
"""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator
from typing_extensions import TypedDict


# ============ エージェント状態 ============

class InvocationState(TypedDict, total=False):
    """エージェント呼び出し時の状態データ（invocation_state の型定義）"""
    session_id: str
    applicant_name: str
    application_date: str


# ============ 定数 ============

TRANSPORT_TYPE_MAP: Dict[str, str] = {
    "train": "電車",
    "鉄道": "電車",
    "地下鉄": "電車",
    "電車": "電車",
    "bus": "バス",
    "バス": "バス",
    "taxi": "タクシー",
    "cab": "タクシー",
    "タクシー": "タクシー",
    "airplane": "飛行機",
    "plane": "飛行機",
    "飛行機": "飛行機",
}

EXPENSE_CATEGORY_MAP: Dict[str, str] = {
    "文房具": "事務用品費",
    "事務用品": "事務用品費",
    "消耗品": "事務用品費",
    "事務用品費": "事務用品費",
    "ホテル": "宿泊費",
    "旅館": "宿泊費",
    "宿泊": "宿泊費",
    "宿泊費": "宿泊費",
    "資格": "資格精算費",
    "検定": "資格精算費",
    "資格精算費": "資格精算費",
    "その他": "その他経費",
    "その他経費": "その他経費",
}


# ============ 共通バリデーター ============

def parse_date(v: Any) -> date:
    """文字列をdatetime.dateに変換する共通バリデーター"""
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, str):
        v = v.strip()
        try:
            return datetime.strptime(v, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"日付の形式が不正です。YYYY-MM-DD形式で入力してください。（入力値: {v!r}）")
    raise ValueError(f"日付に変換できない型です: {type(v)}")


def normalize_transport_type(v: Any) -> str:
    """交通手段を正規化する共通バリデーター"""
    if not isinstance(v, str):
        raise ValueError("交通手段は文字列で入力してください。")
    normalized = TRANSPORT_TYPE_MAP.get(v.strip())
    if normalized is None:
        allowed = list(set(TRANSPORT_TYPE_MAP.values()))
        raise ValueError(
            f"交通手段の値が不正です。「電車」「バス」「タクシー」「飛行機」のいずれかを入力してください。（入力値: {v!r}）"
        )
    return normalized


def normalize_expense_category(v: Any) -> str:
    """経費区分を正規化する共通バリデーター"""
    if not isinstance(v, str):
        raise ValueError("経費区分は文字列で入力してください。")
    normalized = EXPENSE_CATEGORY_MAP.get(v.strip())
    if normalized is None:
        raise ValueError(
            f"経費区分の値が不正です。「事務用品費」「宿泊費」「資格精算費」「その他経費」のいずれかを入力してください。（入力値: {v!r}）"
        )
    return normalized


def parse_amount(v: Any) -> int:
    """金額文字列をintに変換するヘルパー関数。"1,000円" → 1000"""
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return int(v)
    if isinstance(v, str):
        cleaned = v.strip().replace(",", "").replace("円", "").replace("¥", "").replace("￥", "")
        try:
            return int(cleaned)
        except ValueError:
            raise ValueError(f"金額に変換できません: {v!r}")
    raise ValueError(f"金額に変換できない型です: {type(v)}")


# ============ 汎用入力モデル ============

class UserInputText(BaseModel):
    """ユーザー入力テキストの汎用モデル"""
    text: str = Field(..., min_length=1, max_length=500, description="ユーザー入力テキスト")


# ============ マスタデータモデル ============

class TrainFareRecord(BaseModel):
    """電車区間運賃レコード（train_routes.json の1エントリ）"""
    departure: str = Field(..., min_length=1, description="出発駅")
    destination: str = Field(..., min_length=1, description="到着駅")
    fare: int = Field(..., ge=0, description="区間運賃（円）")

    @field_validator("fare", mode="before")
    @classmethod
    def validate_fare(cls, v: Any) -> int:
        if isinstance(v, str):
            return parse_amount(v)
        return v


# ============ ツール入力モデル ============

class TransportExpenseCalculatorInput(BaseModel):
    """交通費計算ツール入力モデル（calculate_transport_expense 用）"""
    transport_date: date = Field(..., description="移動日（YYYY-MM-DD形式）")
    departure: str = Field(..., min_length=1, description="出発地")
    destination: str = Field(..., min_length=1, description="目的地")
    transport_type: Literal["電車", "バス", "タクシー", "飛行機"] = Field(
        ..., description="交通手段"
    )

    @field_validator("transport_date", mode="before")
    @classmethod
    def validate_transport_date(cls, v: Any) -> date:
        return parse_date(v)

    @field_validator("transport_type", mode="before")
    @classmethod
    def validate_transport_type(cls, v: Any) -> str:
        return normalize_transport_type(v)

    @field_validator("departure", "destination", mode="before")
    @classmethod
    def strip_whitespace(cls, v: Any) -> str:
        if isinstance(v, str):
            stripped = v.strip()
            if not stripped:
                raise ValueError("空白のみの値は入力できません。")
            return stripped
        return v


# ============ 出力生成モデル ============

class TransportItem(BaseModel):
    """交通費申請書の移動区間明細"""
    no: int = Field(..., ge=1, description="行番号")
    transport_date: str = Field(..., description="移動日（YYYY-MM-DD形式）")
    departure: str = Field(..., min_length=1, description="出発地")
    destination: str = Field(..., min_length=1, description="目的地")
    transport_type: str = Field(..., min_length=1, description="交通手段")
    amount: int = Field(..., ge=0, description="費用（円）")
    business_purpose: str = Field(..., min_length=1, description="業務目的")


class TransportApplicationFormInput(BaseModel):
    """交通費精算申請書生成ツール入力モデル"""
    applicant_name: str = Field(..., min_length=1, max_length=100, description="申請者名")
    application_date: date = Field(..., description="申請日")
    items: List[TransportItem] = Field(..., description="移動区間リスト")
    business_purpose: str = Field(..., min_length=1, description="業務目的")

    @field_validator("application_date", mode="before")
    @classmethod
    def validate_application_date(cls, v: Any) -> date:
        return parse_date(v)

    @field_validator("applicant_name", "business_purpose", mode="before")
    @classmethod
    def strip_fields(cls, v: Any) -> str:
        if isinstance(v, str):
            return v.strip()
        return v

    @model_validator(mode="after")
    def validate_items_not_empty(self) -> "TransportApplicationFormInput":
        if not self.items:
            raise ValueError("移動区間が入力されていません。少なくとも1件の移動区間を入力してください。")
        return self


class ExpenseItem(BaseModel):
    """経費申請書の経費明細"""
    no: int = Field(..., ge=1, description="行番号")
    purchase_date: str = Field(..., description="購入日（YYYY-MM-DD形式）")
    store_name: str = Field(..., min_length=1, description="店舗名")
    item_name: str = Field(..., min_length=1, description="品目")
    expense_category: str = Field(..., min_length=1, description="経費区分")
    amount: int = Field(..., ge=0, description="金額（円）")
    business_purpose: str = Field(..., min_length=1, description="業務目的")


class ExpenseApplicationFormInput(BaseModel):
    """経費精算申請書生成ツール入力モデル"""
    applicant_name: str = Field(..., min_length=1, max_length=100, description="申請者名")
    application_date: date = Field(..., description="申請日")
    items: List[ExpenseItem] = Field(..., description="経費明細リスト")
    business_purpose: str = Field(..., min_length=1, description="業務目的")

    @field_validator("application_date", mode="before")
    @classmethod
    def validate_application_date(cls, v: Any) -> date:
        return parse_date(v)

    @field_validator("applicant_name", "business_purpose", mode="before")
    @classmethod
    def strip_fields(cls, v: Any) -> str:
        if isinstance(v, str):
            return v.strip()
        return v

    @model_validator(mode="after")
    def validate_items_not_empty(self) -> "ExpenseApplicationFormInput":
        if not self.items:
            raise ValueError("経費明細が入力されていません。少なくとも1件の経費明細を入力してください。")
        return self
