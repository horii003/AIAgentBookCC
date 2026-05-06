# 参照: DD-01a 交通費計算ツール詳細設計書, DD-01b 申請書生成ツール詳細設計書, BD-02 データモデル基本設計書
"""データモデルの定義

全コンポーネント（AG-001〜AG-003・TOOL-001・TOOL-002）で使用するデータ構造を一元管理し、
型安全性を保証する。Pydantic v2の field_validator・model_validator による宣言的バリデーション・
正規化で業務ルール（BRL-14/BRL-15/BRL-17/BRL-12等）を実装する。
"""
from datetime import date, timedelta
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator

try:
    from dateutil import parser as dateutil_parser
except ImportError:
    dateutil_parser = None


# ============ 共通バリデーター ============

def normalize_station_name(v: str) -> str:
    """駅名から「駅」「駅前」接尾語を除去して正規化する（BRL-15）。

    Args:
        v: 駅名文字列（「渋谷駅」「渋谷駅前」等）

    Returns:
        正規化済み駅名（「渋谷」等）
    """
    if v is None:
        return v
    v = v.strip()
    # BRL-15: 「駅前」を優先して除去し、次に「駅」を除去する
    if v.endswith("駅前"):
        v = v[:-2]
    elif v.endswith("駅"):
        v = v[:-1]
    return v


def normalize_transport_type(v: str) -> str:
    """交通手段の表記ゆれを「電車」「バス」「タクシー」「飛行機」に正規化する（BRL-14）。

    Args:
        v: 交通手段文字列（「JR」「鉄道」等）

    Returns:
        正規化済み交通手段（「電車」「バス」「タクシー」「飛行機」のいずれか）

    Raises:
        ValueError: マッピングにない値の場合
    """
    # BRL-14: 交通手段の表記ゆれ正規化マッピング
    transport_map = {
        "電車": "電車",
        "鉄道": "電車",
        "JR": "電車",
        "地下鉄": "電車",
        "電鉄": "電車",
        "バス": "バス",
        "路線バス": "バス",
        "タクシー": "タクシー",
        "taxi": "タクシー",
        "飛行機": "飛行機",
        "航空機": "飛行機",
        "airplane": "飛行機",
    }
    if v in transport_map:
        return transport_map[v]
    raise ValueError(
        f"交通手段のエラー: 「{v}」は対応していません。電車・バス・タクシー・飛行機のいずれかを指定してください"
    )


def normalize_expense_category(v: str) -> str:
    """経費区分の表記ゆれを「事務用品費」「宿泊費」「資格精算費」「その他経費」に正規化する（BRL-17）。

    Args:
        v: 経費区分文字列（「事務用品」「宿泊」等）

    Returns:
        正規化済み経費区分。判断不可時は「その他経費」を返す（エラーにしない）
    """
    # BRL-17: 経費区分の表記ゆれ正規化マッピング
    category_map = {
        "事務用品費": "事務用品費",
        "事務用品": "事務用品費",
        "宿泊費": "宿泊費",
        "宿泊": "宿泊費",
        "資格精算費": "資格精算費",
        "資格費": "資格精算費",
        "資格": "資格精算費",
        "その他経費": "その他経費",
    }
    # BRL-17: 判断不可時は「その他経費」として扱う（エラーにしない）
    return category_map.get(v, "その他経費")


def parse_date_field(v) -> Optional[date]:
    """文字列入力をPythonのdate型に変換する。

    Args:
        v: 日付文字列（YYYY-MM-DD等の各種フォーマット）またはdateオブジェクト

    Returns:
        date型の日付。Noneの場合はNoneを返す

    Raises:
        ValueError: 変換失敗時
    """
    if v is None:
        return None
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        if not v.strip():
            raise ValueError("日付のエラー: 正しい日付形式（YYYY-MM-DD）で入力してください")
        try:
            if dateutil_parser is not None:
                return dateutil_parser.parse(v).date()
            else:
                # python-dateutilがない場合はisoformat形式のみ対応
                return date.fromisoformat(v)
        except Exception:
            raise ValueError("日付のエラー: 正しい日付形式（YYYY-MM-DD）で入力してください")
    raise ValueError("日付のエラー: 正しい日付形式（YYYY-MM-DD）で入力してください")


def validate_positive_amount(v: int) -> int:
    """金額が1円以上の正整数であることを検証する。

    Args:
        v: 金額（円単位）

    Returns:
        検証済みの金額

    Raises:
        ValueError: 0以下の値の場合
    """
    # 1以上の正整数チェック
    if v is None or v <= 0:
        raise ValueError("金額のエラー: 1円以上の金額を入力してください")
    return v


def validate_required_string(v: str, max_length: int = 500) -> str:
    """必須文字列フィールドが空でないこと・最大文字数以内であることを検証する。前後空白を自動除去する。

    Args:
        v: 文字列値
        max_length: 最大文字数（デフォルト500文字。GRD-012）

    Returns:
        前後空白を除去した文字列

    Raises:
        ValueError: 空文字・Noneまたは文字数超過の場合
    """
    if v is None or (isinstance(v, str) and not v.strip()):
        raise ValueError("入力のエラー: 必須項目が入力されていません。入力してください")
    v = v.strip()
    # GRD-012: 500文字以内制限
    if len(v) > max_length:
        raise ValueError(f"入力のエラー: {max_length}文字以内で入力してください")
    return v


# ============ マスタデータモデル ============

class RailwayRouteMaster(BaseModel):
    """DATA-009（train_routes.json）の1レコードを表すマスタデータモデル。

    責務: 電車経路・運賃データの型安全なパース・バリデーションを行う。
    制約: fareは正の整数であること。
    """
    route_id: str = Field(..., description="区間識別キー", min_length=1)
    departure: str = Field(..., description="出発地（正規化済み駅名）", min_length=1)
    destination: str = Field(..., description="目的地（正規化済み駅名）", min_length=1)
    fare: int = Field(..., description="運賃（円単位）", gt=0)


# ============ ツール入力モデル ============

class FareCalculationInput(BaseModel):
    """TOOL-001（calculate_transport_fare）への入力バリデーション・正規化モデル。

    責務: 運賃計算ツールへの入力パラメータの型安全性と正規化を保証する。
    制約:
      - departure・destination: 空文字禁止・500文字以内・接尾語（駅/駅前）自動除去（BRL-15）
      - transport_type: 「電車」「バス」「タクシー」「飛行機」への正規化（BRL-14）
      - travel_date: 任意フィールド。YYYY-MM-DD等の解析可能形式
    """
    departure: str = Field(..., description="出発地", min_length=1, max_length=500)
    destination: str = Field(..., description="目的地", min_length=1, max_length=500)
    transport_type: Literal["電車", "バス", "タクシー", "飛行機"] = Field(
        ..., description="交通手段"
    )
    travel_date: Optional[date] = Field(None, description="移動日（YYYY-MM-DD形式）")

    # BRL-15: 駅名正規化（接尾語除去）
    @field_validator("departure", "destination", mode="before")
    @classmethod
    def normalize_station(cls, v: str) -> str:
        """駅名の接尾語を除去して正規化する（BRL-15）。"""
        if not v or not isinstance(v, str) or not v.strip():
            raise ValueError("入力のエラー: 必須項目が入力されていません。入力してください")
        v = v.strip()
        if len(v) > 500:
            raise ValueError("入力のエラー: 500文字以内で入力してください")
        return normalize_station_name(v)

    # BRL-14: 交通手段の表記ゆれ正規化
    @field_validator("transport_type", mode="before")
    @classmethod
    def normalize_transport(cls, v: str) -> str:
        """交通手段の表記ゆれを正規化する（BRL-14）。"""
        return normalize_transport_type(v)

    # 移動日の文字列→date変換
    @field_validator("travel_date", mode="before")
    @classmethod
    def parse_travel_date(cls, v) -> Optional[date]:
        """移動日文字列をdate型に変換する。"""
        return parse_date_field(v)


class TransportSegment(BaseModel):
    """交通費申請の1区間移動情報を表すモデル（TransportApplicationDataのリスト要素）。

    責務: 移動区間の必須項目を型安全に保持する。
    制約:
      - travel_date: 必須。YYYY-MM-DD等の解析可能形式
      - fare: 1以上の正整数（BRL-06）
    """
    travel_date: date = Field(..., description="移動日")
    departure: str = Field(..., description="出発地（正規化済み）", min_length=1)
    destination: str = Field(..., description="目的地（正規化済み）", min_length=1)
    transport_type: Literal["電車", "バス", "タクシー", "飛行機"] = Field(
        ..., description="交通手段"
    )
    fare: int = Field(..., description="運賃（円単位）", gt=0)

    # 移動日の文字列→date変換
    @field_validator("travel_date", mode="before")
    @classmethod
    def parse_travel_date(cls, v) -> date:
        """移動日文字列をdate型に変換する。"""
        result = parse_date_field(v)
        if result is None:
            raise ValueError("日付のエラー: 正しい日付形式（YYYY-MM-DD）で入力してください")
        return result


class TransportApplicationData(BaseModel):
    """TOOL-002a（generate_transport_application）への入力バリデーションモデル。

    責務: 交通費申請書生成に必要な全必須項目を型安全に保持する。
    制約:
      - segments: 1件以上必須（BRL-06）
      - applicant_name・purpose: 空文字禁止・500文字以内
      - application_date: YYYY-MM-DD等の解析可能形式
    """
    applicant_name: str = Field(..., description="申請者名", min_length=1, max_length=500)
    application_date: date = Field(..., description="申請日")
    segments: list[TransportSegment] = Field(..., description="移動区間リスト（1件以上）")
    purpose: str = Field(..., description="業務目的", min_length=1, max_length=500)

    @field_validator("applicant_name", "purpose", mode="before")
    @classmethod
    def validate_required_str(cls, v: str) -> str:
        """必須文字列フィールドの検証（空文字禁止・500文字以内）。"""
        return validate_required_string(v)

    @field_validator("application_date", mode="before")
    @classmethod
    def parse_application_date(cls, v) -> date:
        """申請日文字列をdate型に変換する。"""
        result = parse_date_field(v)
        if result is None:
            raise ValueError("日付のエラー: 申請日が正しく設定されていません。")
        return result

    @field_validator("segments", mode="before")
    @classmethod
    def validate_segments_not_empty(cls, v) -> list:
        """移動区間リストが1件以上であることを確認する（BRL-06）。"""
        if not v or len(v) == 0:
            raise ValueError("移動区間情報のエラー: 移動区間が1件以上必要です")
        return v


class ExpenseApplicationData(BaseModel):
    """TOOL-002b（generate_expense_application）への入力バリデーションモデル。

    責務: 経費申請書生成に必要な全必須項目を型安全に保持する。
    制約:
      - applicant_name・store_name・purpose: 空文字禁止・500文字以内
      - expense_category: 「事務用品費」「宿泊費」「資格精算費」「その他経費」への正規化（BRL-17）
      - amount: 1以上の正整数（BRL-07）
      - expense_date: YYYY-MM-DD等の解析可能形式
      - 申請期限チェック（BRL-12）: application_date - expense_date <= 90日（model_validatorで実施）
    """
    applicant_name: str = Field(..., description="申請者名", min_length=1, max_length=500)
    application_date: date = Field(..., description="申請日")
    store_name: str = Field(..., description="店舗名", min_length=1, max_length=500)
    expense_category: Literal["事務用品費", "宿泊費", "資格精算費", "その他経費"] = Field(
        ..., description="経費区分"
    )
    amount: int = Field(..., description="金額（円単位）", gt=0)
    expense_date: date = Field(..., description="経費発生日")
    purpose: str = Field(..., description="業務目的", min_length=1, max_length=500)

    @field_validator("applicant_name", "store_name", "purpose", mode="before")
    @classmethod
    def validate_required_str(cls, v: str) -> str:
        """必須文字列フィールドの検証（空文字禁止・500文字以内）。"""
        return validate_required_string(v)

    @field_validator("application_date", "expense_date", mode="before")
    @classmethod
    def parse_dates(cls, v) -> date:
        """日付文字列をdate型に変換する。"""
        result = parse_date_field(v)
        if result is None:
            raise ValueError("日付のエラー: 正しい日付形式（YYYY-MM-DD）で入力してください")
        return result

    @field_validator("expense_category", mode="before")
    @classmethod
    def normalize_category(cls, v: str) -> str:
        """経費区分の表記ゆれを正規化する（BRL-17）。"""
        return normalize_expense_category(v)

    @model_validator(mode="after")
    def check_application_deadline(self) -> "ExpenseApplicationData":
        """申請期限チェック（BRL-12）: 経費発生日から申請日まで90日以内であることを確認する。"""
        # BRL-12: (application_date - expense_date).days <= 90
        if self.application_date and self.expense_date:
            days_diff = (self.application_date - self.expense_date).days
            if days_diff > 90:
                raise ValueError(
                    f"申請のエラー: 申請期限（経費発生日から90日以内）を超過しています"
                    f"（経費発生日: {self.expense_date.isoformat()}、"
                    f"申請日: {self.application_date.isoformat()}）。"
                    f"対処方法: 担当部署へご相談ください。"
                )
        return self
