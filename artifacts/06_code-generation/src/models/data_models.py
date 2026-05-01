"""データモデルの定義

業務ドメインに応じたPydanticモデルを定義する。
各モデルはツール入力、エージェント状態、マスタデータの型安全性を保証する。
"""
from datetime import date
from typing import Optional, List, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ============ 共通バリデーター ============

def normalize_station_name(v: str) -> str:
    """駅名の正規化（末尾の「駅」「Station」を除去し、前後の空白をtrim）"""
    v = v.strip()
    if v.endswith("駅"):
        v = v[:-1]
    if v.lower().endswith("station"):
        v = v[: -len("station")].strip()
    return v


def normalize_transport_type(v: str) -> str:
    """交通手段の正規化（英語・略称→日本語正規値）"""
    mapping = {
        "train": "電車",
        "鉄道": "電車",
        "電鉄": "電車",
        "bus": "バス",
        "taxi": "タクシー",
        "cab": "タクシー",
        "airplane": "飛行機",
        "plane": "飛行機",
        "aircraft": "飛行機",
    }
    normalized = mapping.get(v.strip().lower(), v.strip())
    return normalized


def validate_date(v: str) -> date:
    """日付文字列のバリデーション（YYYY-MM-DD形式）"""
    if isinstance(v, date):
        return v
    try:
        return date.fromisoformat(str(v))
    except (ValueError, TypeError):
        raise ValueError("移動日の形式が不正です。YYYY-MM-DD 形式で入力してください。")


def validate_business_purpose(v: str) -> str:
    """業務目的のバリデーション（空文字・空白のみ禁止）"""
    if not v or not v.strip():
        raise ValueError("業務目的が入力されていません。業務目的を入力してください。")
    return v


def validate_amount(v: int) -> int:
    """金額のバリデーション（1以上の整数）"""
    if v is None or v < 1:
        raise ValueError("費用は1円以上を入力してください。")
    return v


def normalize_expense_category(v: str) -> str:
    """経費区分の正規化（略称・別表記→正規値、判断不能→「その他経費」）"""
    mapping = {
        "事務用品": "事務用品費",
        "文房具": "事務用品費",
        "備品": "事務用品費",
        "宿泊": "宿泊費",
        "ホテル": "宿泊費",
        "出張宿泊": "宿泊費",
        "資格": "資格取得費",
        "試験": "資格取得費",
        "資格試験": "資格取得費",
        "その他": "その他経費",
        "雑費": "その他経費",
    }
    normalized = mapping.get(v.strip(), v.strip())
    valid_categories = {"事務用品費", "宿泊費", "資格取得費", "その他経費"}
    if normalized not in valid_categories:
        return "その他経費"
    return normalized


# ============ エージェント状態モデル ============

class InvocationState(BaseModel):
    """エージェント呼び出し時の状態データ"""
    session_id: Optional[str] = Field(None, description="セッションID")
    applicant_name: str = Field(default="", description="申請者名")
    application_date: str = Field(..., description="申請日（YYYY-MM-DD形式）")


# ============ ツール入力モデル ============

class TransportCalculatorInput(BaseModel):
    """交通費計算ツールの入力モデル"""
    model_config = ConfigDict(populate_by_name=True)

    transport_type: Literal["電車", "バス", "タクシー", "飛行機"] = Field(
        ..., description="交通手段"
    )
    departure: str = Field(..., min_length=1, description="出発地")
    destination: str = Field(..., min_length=1, description="目的地")
    travel_date: date = Field(..., description="移動日（YYYY-MM-DD形式）")

    @field_validator("transport_type", mode="before")
    @classmethod
    def _normalize_transport(cls, v: str) -> str:
        """交通手段を正規化する"""
        return normalize_transport_type(v)

    @field_validator("departure", "destination", mode="before")
    @classmethod
    def _normalize_station(cls, v: str) -> str:
        """駅名を正規化する"""
        return normalize_station_name(v)

    @field_validator("travel_date", mode="before")
    @classmethod
    def _validate_travel_date(cls, v) -> date:
        """移動日を検証する"""
        return validate_date(v)


# ============ 出力生成モデル ============

class TransportSegment(BaseModel):
    """移動区間データ"""
    travel_date: str = Field(..., description="移動日（YYYY-MM-DD形式）")
    departure: str = Field(..., min_length=1, description="出発地")
    destination: str = Field(..., min_length=1, description="目的地")
    transport_type: Literal["電車", "バス", "タクシー", "飛行機"] = Field(
        ..., description="交通手段"
    )
    fare: int = Field(..., gt=0, description="運賃（円単位）")
    business_purpose: str = Field(..., min_length=1, description="業務目的")

    @model_validator(mode="before")
    @classmethod
    def _normalize_keys(cls, data):
        if isinstance(data, dict) and "business_purpose" not in data and "purpose" in data:
            data = dict(data)
            data["business_purpose"] = data.pop("purpose")
        return data

    @field_validator("transport_type", mode="before")
    @classmethod
    def _normalize_transport(cls, v: str) -> str:
        """交通手段を正規化する"""
        return normalize_transport_type(v)

    @field_validator("departure", "destination", mode="before")
    @classmethod
    def _normalize_station(cls, v: str) -> str:
        """駅名を正規化する"""
        return normalize_station_name(v)


class TransportApplicationInput(BaseModel):
    """交通費精算申請書生成の入力モデル"""
    business_purpose: str = Field(..., min_length=1, description="業務目的")
    segments: List[TransportSegment] = Field(..., min_length=1, description="移動区間リスト（1件以上必須）")

    @field_validator("business_purpose")
    @classmethod
    def _validate_purpose(cls, v: str) -> str:
        """業務目的を検証する"""
        return validate_business_purpose(v)


class ExpenseItem(BaseModel):
    """経費明細データ"""
    purchase_date: str = Field(..., description="購入日（YYYY-MM-DD形式）")
    store_name: str = Field(..., min_length=1, description="購入先・店舗名")
    item_name: str = Field(..., min_length=1, description="購入品目")
    amount: int = Field(..., gt=0, description="金額（円単位）")
    expense_category: str = Field(..., description="経費区分")

    @field_validator("expense_category", mode="before")
    @classmethod
    def _normalize_category(cls, v: str) -> str:
        """経費区分を正規化する"""
        return normalize_expense_category(v)


class ExpenseApplicationInput(BaseModel):
    """経費精算申請書生成の入力モデル"""
    business_purpose: str = Field(..., min_length=1, description="業務目的")
    expense_items: List[ExpenseItem] = Field(..., min_length=1, description="経費明細リスト（1件以上必須）")

    @field_validator("business_purpose")
    @classmethod
    def _validate_purpose(cls, v: str) -> str:
        """業務目的を検証する"""
        return validate_business_purpose(v)
