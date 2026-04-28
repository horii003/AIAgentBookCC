"""データモデルの定義

業務ドメインに応じたPydanticモデルを定義する。
各モデルはツール入力、エージェント状態、マスタデータの型安全性を保証する。
"""
from __future__ import annotations

import re
from datetime import date
from typing import Any, Literal, Optional

from dateutil import parser as dateutil_parser
from pydantic import BaseModel, Field, field_validator, model_validator


# ============ 定数マッピング ============

TRANSPORT_TYPE_MAP: dict[str, str] = {
    "train": "電車",
    "鉄道": "電車",
    "地下鉄": "電車",
    "bus": "バス",
    "taxi": "タクシー",
    "cab": "タクシー",
    "airplane": "飛行機",
    "plane": "飛行機",
}

EXPENSE_CATEGORY_MAP: dict[str, str] = {
    "文房具": "事務用品費",
    "事務用品": "事務用品費",
    "消耗品": "事務用品費",
    "ホテル": "宿泊費",
    "旅館": "宿泊費",
    "宿泊": "宿泊費",
    "資格": "資格精算費",
    "検定": "資格精算費",
    "その他": "その他経費",
}


# ============ 共通ヘルパー関数 ============

def parse_amount(v: Any) -> int:
    """金額文字列を整数に変換する。

    "1,000円" → 1000、"500" → 500、int → そのまま返す。
    """
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return int(v)
    if isinstance(v, str):
        cleaned = re.sub(r"[^\d]", "", v)
        if cleaned == "":
            raise ValueError(f"金額を数値に変換できません: {v!r}")
        return int(cleaned)
    raise ValueError(f"金額のエラー: 0以上の整数で入力してください。受け取った値: {v!r}")


_DATE_YYYYMMDD_RE = re.compile(r"^\d{8}$")

def parse_date(v: Any) -> date:
    """日付文字列を datetime.date に変換する。

    YYYY-MM-DD形式または dateutil.parser でパース可能な文字列を受け付ける。
    8桁連続数字（"20260428" 等）は不正形式として拒否する。
    """
    if isinstance(v, date):
        return v
    if not isinstance(v, str) or v.strip() == "":
        raise ValueError(
            "移動日のエラー: 日付形式が不正です。\n"
            "対処方法: YYYY-MM-DD形式（例: 2026-04-28）で入力してください。"
        )
    if _DATE_YYYYMMDD_RE.match(v.strip()):
        raise ValueError(
            "移動日のエラー: 日付形式が不正です。\n"
            "対処方法: YYYY-MM-DD形式（例: 2026-04-28）で入力してください。"
        )
    try:
        return dateutil_parser.parse(v).date()
    except Exception:
        raise ValueError(
            "移動日のエラー: 日付形式が不正です。\n"
            "対処方法: YYYY-MM-DD形式（例: 2026-04-28）で入力してください。"
        )


def normalize_transport_type(v: Any) -> Any:
    """交通手段を正規化する。TRANSPORT_TYPE_MAP に存在する値は変換し、ない値はそのまま返す。"""
    if isinstance(v, str):
        return TRANSPORT_TYPE_MAP.get(v, v)
    return v


# ============ エージェント状態モデル ============

class InvocationState(BaseModel):
    """エージェント呼び出し時の状態データ"""

    session_id: Optional[str] = Field(None, description="セッションID")
    applicant_name: Optional[str] = Field(None, description="申請者名")
    application_date: Optional[str] = Field(None, description="申請日（YYYY-MM-DD形式）")


# ============ ユーザー入力モデル ============

class UserInputText(BaseModel):
    """ユーザー入力テキストのバリデーション（GRD-001/GRD-017）"""

    text: str = Field(..., min_length=1, max_length=500, description="ユーザー入力テキスト（1〜500文字）")


# ============ マスタデータモデル ============

class TrainFareRecord(BaseModel):
    """電車経路運賃レコード（DATA-011: train_routes.json）"""

    departure: str = Field(..., min_length=1, description="出発駅名")
    destination: str = Field(..., min_length=1, description="到着駅名")
    fare: int = Field(..., ge=0, description="区間運賃（円）")

    @field_validator("fare", mode="before")
    @classmethod
    def validate_fare(cls, v: Any) -> int:
        if not isinstance(v, int) or v < 0:
            raise ValueError(f"運賃は0以上の整数である必要があります: {v!r}")
        return v


# ============ ツール入力モデル ============

class TravelExpenseCalculatorInput(BaseModel):
    """calculate_travel_expense ツール入力バリデーション"""

    travel_date: date = Field(..., description="移動日（YYYY-MM-DD形式）")
    departure: str = Field(..., min_length=1, description="出発地（正規化済み駅名または地名）")
    destination: str = Field(..., min_length=1, description="目的地（正規化済み駅名または地名）")
    transport_type: Literal["電車", "バス", "タクシー", "飛行機"] = Field(
        ..., description="交通手段"
    )

    @field_validator("travel_date", mode="before")
    @classmethod
    def _parse_date(cls, v: Any) -> date:
        return parse_date(v)

    @field_validator("transport_type", mode="before")
    @classmethod
    def _normalize_transport_type(cls, v: Any) -> Any:
        return normalize_transport_type(v)

    @field_validator("departure", "destination", mode="before")
    @classmethod
    def _strip_whitespace(cls, v: Any) -> Any:
        if isinstance(v, str):
            stripped = v.strip()
            if stripped == "":
                raise ValueError("出発地または目的地が入力されていません。入力してください。")
            return stripped
        return v


# ============ 出力生成モデル ============

class TravelItem(BaseModel):
    """交通費精算申請書の移動区間1件分"""

    travel_date: str = Field(..., description="移動日（YYYY-MM-DD形式）")
    departure: str = Field(..., min_length=1, description="出発地")
    destination: str = Field(..., min_length=1, description="目的地")
    transport_type: str = Field(..., description="交通手段")
    amount: int = Field(..., ge=0, description="費用（円）")

    @field_validator("amount", mode="before")
    @classmethod
    def _parse_amount(cls, v: Any) -> int:
        result = parse_amount(v)
        if result < 0:
            raise ValueError("金額のエラー: 0以上の整数で入力してください。")
        return result


class TravelApplicationFormInput(BaseModel):
    """generate_travel_expense_form ツール入力バリデーション"""

    applicant_name: str = Field(..., min_length=1, description="申請者名")
    application_date: str = Field(..., description="申請日（YYYY-MM-DD形式）")
    items: list[TravelItem] = Field(..., description="移動区間リスト（1件以上）")
    business_purpose: str = Field(..., min_length=1, description="業務目的（BRL-20）")

    @model_validator(mode="after")
    def _check_items_not_empty(self) -> "TravelApplicationFormInput":
        if len(self.items) == 0:
            raise ValueError("申請明細が1件以上必要です。移動情報を入力してください。")
        return self

    @field_validator("business_purpose", mode="before")
    @classmethod
    def _strip_purpose(cls, v: Any) -> Any:
        if isinstance(v, str):
            stripped = v.strip()
            if stripped == "":
                raise ValueError(
                    "業務目的が入力されていません。申請の業務目的を入力してください。"
                )
            return stripped
        return v


class ExpenseItem(BaseModel):
    """経費精算申請書の経費明細1件分"""

    expense_date: str = Field(..., description="経費発生日（YYYY-MM-DD形式）")
    category: str = Field(..., description="経費カテゴリ")
    amount: int = Field(..., ge=0, description="金額（円）")
    purpose: str = Field(..., min_length=1, description="業務目的")

    @field_validator("amount", mode="before")
    @classmethod
    def _parse_amount(cls, v: Any) -> int:
        result = parse_amount(v)
        if result < 0:
            raise ValueError("金額のエラー: 0以上の整数で入力してください。")
        return result

    @field_validator("category", mode="before")
    @classmethod
    def _normalize_category(cls, v: Any) -> Any:
        if isinstance(v, str):
            return EXPENSE_CATEGORY_MAP.get(v, v)
        return v


class ExpenseApplicationFormInput(BaseModel):
    """generate_expense_form ツール入力バリデーション"""

    applicant_name: str = Field(..., min_length=1, description="申請者名")
    application_date: str = Field(..., description="申請日（YYYY-MM-DD形式）")
    items: list[ExpenseItem] = Field(..., description="経費明細リスト（1件以上）")

    @model_validator(mode="after")
    def _check_items_not_empty(self) -> "ExpenseApplicationFormInput":
        if len(self.items) == 0:
            raise ValueError("申請明細が1件以上必要です。経費情報を入力してください。")
        return self
