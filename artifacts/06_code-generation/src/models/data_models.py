"""データモデルの定義

業務ドメインに応じたPydanticモデルを定義する。
各モデルはツール入力、エージェント状態、マスタデータの型安全性を保証する。
"""
from datetime import date
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from dateutil import parser as dateutil_parser


# ============ 共通バリデーター ============

def validate_non_empty_string(v: str) -> str:
    """空文字・500文字超チェック"""
    if isinstance(v, str):
        stripped = v.strip()
        if not stripped:
            raise ValueError("この項目は必須です。入力内容を確認してください")
        if len(stripped) > 500:
            raise ValueError("入力内容が長すぎます。500文字以内で入力してください")
    return v


def parse_date(v) -> date:
    """文字列（YYYY-MM-DD / YYYY/MM/DD / YYYY年MM月DD日）を datetime.date に変換する"""
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        try:
            return dateutil_parser.parse(v).date()
        except Exception:
            raise ValueError("日付の形式が不正です。YYYY-MM-DD形式で入力してください（例: 2026-07-03）")
    raise ValueError("日付の形式が不正です。YYYY-MM-DD形式で入力してください（例: 2026-07-03）")


def normalize_station_name(v: str) -> str:
    """末尾「駅」を除去する"""
    if isinstance(v, str):
        result = v.removesuffix("駅").strip()
        if not result:
            raise ValueError("駅名を入力してください")
        return result
    return v


def normalize_transport_type(v: str) -> str:
    """交通手段を正規化する"""
    _MAP = {
        "train": "電車", "鉄道": "電車",
        "bus": "バス",
        "taxi": "タクシー",
        "plane": "飛行機", "airplane": "飛行機", "飛行": "飛行機",
    }
    if isinstance(v, str):
        if v in ("電車", "バス", "タクシー", "飛行機"):
            return v
        normalized = _MAP.get(v)
        if normalized:
            return normalized
        raise ValueError("交通手段は電車・バス・タクシー・飛行機のいずれかを入力してください")
    return v


def parse_amount(v) -> int:
    """カンマ・「円」除去後に非負整数変換"""
    if isinstance(v, int):
        if v < 0:
            raise ValueError("金額の形式が不正です。半角数字で入力してください（例: 10000）")
        return v
    if isinstance(v, str):
        cleaned = v.replace(",", "").replace("円", "").strip()
        try:
            amount = int(cleaned)
        except ValueError:
            raise ValueError("金額の形式が不正です。半角数字で入力してください（例: 10000）")
        if amount < 0:
            raise ValueError("金額の形式が不正です。半角数字で入力してください（例: 10000）")
        return amount
    raise ValueError("金額の形式が不正です。半角数字で入力してください（例: 10000）")


def normalize_expense_category(v) -> str:
    """経費区分を正規化する（判断不能時は「その他経費」にフォールバック、ValueError非送出）"""
    _VALID = ("事務用品費", "宿泊費", "資格精算費", "その他経費")
    _MAP = {
        "事務用品": "事務用品費", "文房具": "事務用品費",
        "宿泊": "宿泊費", "ホテル": "宿泊費",
        "資格": "資格精算費", "研修": "資格精算費",
        "その他": "その他経費",
    }
    if isinstance(v, str):
        if v in _VALID:
            return v
        normalized = _MAP.get(v)
        if normalized:
            return normalized
        return "その他経費"
    return v


def normalize_hitl_result(v) -> Optional[str]:
    """HitL承認結果を正規化する"""
    if v is None:
        return None
    _MAP = {
        "ok": "OK", "yes": "OK", "はい": "OK",
        "修正する": "修正",
        "cancel": "キャンセル", "いいえ": "キャンセル",
    }
    if isinstance(v, str):
        if v in ("OK", "修正", "キャンセル"):
            return v
        normalized = _MAP.get(v)
        if normalized:
            return normalized
        raise ValueError("OK・修正・キャンセルのいずれかを選択してください")
    return v


# Pydantic v2 用クラスメソッドラッパー
def _cls_validate_non_empty_string(cls, v):
    return validate_non_empty_string(v)


def _cls_parse_date(cls, v):
    return parse_date(v)


def _cls_normalize_station_name(cls, v):
    return normalize_station_name(v)


def _cls_normalize_transport_type(cls, v):
    return normalize_transport_type(v)


def _cls_parse_amount(cls, v):
    return parse_amount(v)


def _cls_normalize_expense_category(cls, v):
    return normalize_expense_category(v)


def _cls_normalize_hitl_result(cls, v):
    return normalize_hitl_result(v)


# ============ 入力モデル ============

class TransportSectionInput(BaseModel):
    """TOOL-001（交通費計算ツール）への入力パラメータ（1移動区間）"""
    travel_date: date = Field(..., description="移動日（YYYY-MM-DD形式）")
    departure: str = Field(..., description="出発地")
    destination: str = Field(..., description="目的地")
    transport_type: Literal["電車", "バス", "タクシー", "飛行機"] = Field(..., description="交通手段")
    purpose: str = Field(..., description="業務目的")

    _parse_travel_date = field_validator("travel_date", mode="before")(classmethod(_cls_parse_date))
    _normalize_departure = field_validator("departure", mode="before")(classmethod(_cls_normalize_station_name))
    _normalize_destination = field_validator("destination", mode="before")(classmethod(_cls_normalize_station_name))
    _normalize_transport = field_validator("transport_type", mode="before")(classmethod(_cls_normalize_transport_type))
    _validate_purpose = field_validator("purpose")(classmethod(_cls_validate_non_empty_string))


class TransportSection(BaseModel):
    """AG-002 が収集した1移動区間の完成データ（費用確定後）"""
    travel_date: date = Field(..., description="移動日")
    departure: str = Field(..., description="出発地（正規化済み）")
    destination: str = Field(..., description="目的地（正規化済み）")
    transport_type: Literal["電車", "バス", "タクシー", "飛行機"] = Field(..., description="交通手段")
    fare: int = Field(..., description="交通費（円）")
    purpose: str = Field(..., description="業務目的")

    _parse_travel_date = field_validator("travel_date", mode="before")(classmethod(_cls_parse_date))
    _normalize_departure = field_validator("departure", mode="before")(classmethod(_cls_normalize_station_name))
    _normalize_destination = field_validator("destination", mode="before")(classmethod(_cls_normalize_station_name))
    _normalize_transport = field_validator("transport_type", mode="before")(classmethod(_cls_normalize_transport_type))
    _parse_fare = field_validator("fare", mode="before")(classmethod(_cls_parse_amount))
    _validate_purpose = field_validator("purpose")(classmethod(_cls_validate_non_empty_string))


class TransportExpenseFormInput(BaseModel):
    """TOOL-002（申請書生成ツール：交通費用）への入力パラメータ"""
    applicant_name: str = Field(..., description="申請者名")
    application_date: date = Field(..., description="申請日")
    sections: list[TransportSection] = Field(..., description="移動区間リスト（1件以上）")
    total_fare: int = Field(..., description="交通費合計（円）")

    _validate_applicant_name = field_validator("applicant_name")(classmethod(_cls_validate_non_empty_string))
    _parse_application_date = field_validator("application_date", mode="before")(classmethod(_cls_parse_date))
    _parse_total_fare = field_validator("total_fare", mode="before")(classmethod(_cls_parse_amount))

    @model_validator(mode="after")
    def validate_sections_not_empty(self) -> "TransportExpenseFormInput":
        """移動区間リストが1件以上であることを確認"""
        if len(self.sections) < 1:
            raise ValueError("移動区間は1件以上入力してください")
        return self


class ExpenseItem(BaseModel):
    """AG-003 が収集した1経費件の完成データ"""
    purchase_date: date = Field(..., description="購入日")
    store_name: str = Field(..., description="店舗名")
    item_name: str = Field(..., description="品目")
    expense_category: Literal["事務用品費", "宿泊費", "資格精算費", "その他経費"] = Field(..., description="経費区分")
    amount: int = Field(..., description="金額（円）")
    purpose: str = Field(..., description="業務目的")

    _parse_purchase_date = field_validator("purchase_date", mode="before")(classmethod(_cls_parse_date))
    _validate_store_name = field_validator("store_name")(classmethod(_cls_validate_non_empty_string))
    _validate_item_name = field_validator("item_name")(classmethod(_cls_validate_non_empty_string))
    _normalize_category = field_validator("expense_category", mode="before")(classmethod(_cls_normalize_expense_category))
    _parse_amount_field = field_validator("amount", mode="before")(classmethod(_cls_parse_amount))
    _validate_purpose = field_validator("purpose")(classmethod(_cls_validate_non_empty_string))


class GeneralExpenseFormInput(BaseModel):
    """TOOL-002（申請書生成ツール：経費用）への入力パラメータ"""
    applicant_name: str = Field(..., description="申請者名")
    application_date: date = Field(..., description="申請日")
    items: list[ExpenseItem] = Field(..., description="経費リスト（1件以上）")
    total_amount: int = Field(..., description="経費合計（円）")

    _validate_applicant_name = field_validator("applicant_name")(classmethod(_cls_validate_non_empty_string))
    _parse_application_date = field_validator("application_date", mode="before")(classmethod(_cls_parse_date))
    _parse_total_amount = field_validator("total_amount", mode="before")(classmethod(_cls_parse_amount))

    @model_validator(mode="after")
    def validate_items_not_empty(self) -> "GeneralExpenseFormInput":
        """経費リストが1件以上であることを確認"""
        if len(self.items) < 1:
            raise ValueError("経費は1件以上入力してください")
        return self


# ============ 出力モデル ============

class TransportFareOutput(BaseModel):
    """TOOL-001（交通費計算ツール）の出力"""
    fare: int = Field(..., description="計算した交通費（円）", ge=0)
    route_description: str = Field(..., description="計算根拠の説明")
    is_manual_input: bool = Field(False, description="手動入力フォールバックの場合True")


class ApplicationFormOutput(BaseModel):
    """TOOL-002（申請書生成ツール）の出力"""
    file_path: str = Field(..., description="生成された申請書ドラフトのファイルパス")
    status: Literal["SUCCESS", "FAILED"] = Field(..., description="申請書生成の結果ステータス")
    message: str = Field("", description="エラー発生時のメッセージ")


# ============ 内部モデル ============

class CollectedTransportInfo(BaseModel):
    """交通費精算申請の収集済み申請情報全体"""
    applicant_name: str = Field(..., description="申請者名")
    application_date: date = Field(..., description="申請日")
    sections: list[TransportSection] = Field(..., description="移動区間リスト（1件以上）")
    total_fare: int = Field(..., description="交通費合計（円）")

    _validate_applicant_name = field_validator("applicant_name")(classmethod(_cls_validate_non_empty_string))
    _parse_application_date = field_validator("application_date", mode="before")(classmethod(_cls_parse_date))
    _parse_total_fare = field_validator("total_fare", mode="before")(classmethod(_cls_parse_amount))

    @model_validator(mode="after")
    def validate_sections_not_empty(self) -> "CollectedTransportInfo":
        """移動区間リストが1件以上であることを確認"""
        if len(self.sections) < 1:
            raise ValueError("移動区間は1件以上入力してください")
        return self


class CollectedExpenseInfo(BaseModel):
    """経費精算申請の収集済み申請情報全体"""
    applicant_name: str = Field(..., description="申請者名")
    application_date: date = Field(..., description="申請日")
    items: list[ExpenseItem] = Field(..., description="経費リスト（1件以上）")
    total_amount: int = Field(..., description="経費合計（円）")

    _validate_applicant_name = field_validator("applicant_name")(classmethod(_cls_validate_non_empty_string))
    _parse_application_date = field_validator("application_date", mode="before")(classmethod(_cls_parse_date))
    _parse_total_amount = field_validator("total_amount", mode="before")(classmethod(_cls_parse_amount))

    @model_validator(mode="after")
    def validate_items_not_empty(self) -> "CollectedExpenseInfo":
        """経費リストが1件以上であることを確認"""
        if len(self.items) < 1:
            raise ValueError("経費は1件以上入力してください")
        return self


class AgentDelegationMessage(BaseModel):
    """AG-001 から AG-002/AG-003 への委譲リクエストデータ"""
    application_type: Literal["交通費精算申請", "経費精算申請"] = Field(..., description="申請種別名")
    application_form_name: str = Field(..., description="申請書名")
    application_destination: str = Field(..., description="申請先（要件上未定義）")
    judgment_basis: str = Field(..., description="判断根拠（参照ルール名）")
    applicant_name: str = Field(..., description="申請者名")

    _validate_form_name = field_validator("application_form_name")(classmethod(_cls_validate_non_empty_string))
    _validate_destination = field_validator("application_destination")(classmethod(_cls_validate_non_empty_string))
    _validate_judgment = field_validator("judgment_basis")(classmethod(_cls_validate_non_empty_string))
    _validate_applicant = field_validator("applicant_name")(classmethod(_cls_validate_non_empty_string))


# ============ 状態管理モデル ============

class SessionState(BaseModel):
    """セッション全体の状態（DATA-005）"""
    model_config = ConfigDict(use_enum_values=True)

    session_id: str = Field(..., description="セッションID（sess_UUID形式）")
    status: Literal["READY", "RUNNING", "WAITING", "COMPLETED", "FAILED", "TERMINATED"] = Field(
        "READY", description="実行状態"
    )
    iteration: int = Field(0, ge=0, description="対話回数カウント")
    current_step: str = Field("", description="現在の処理ステップ名")
    application_type: Optional[Literal["交通費精算申請", "経費精算申請"]] = Field(None, description="確定した申請種別")
    hitl_result: Optional[Literal["OK", "修正", "キャンセル"]] = Field(None, description="HitL承認結果")

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        """session_idが sess_ プレフィックスを持つことを確認"""
        if not v.startswith("sess_"):
            raise ValueError("session_idはsess_プレフィックスが必要です")
        return v

    _normalize_hitl = field_validator("hitl_result", mode="before")(classmethod(_cls_normalize_hitl_result))


class ApplicationContext(BaseModel):
    """申請フローのコンテキスト"""
    applicant_name: str = Field(..., description="申請者名")
    application_date: date = Field(..., description="申請日")
    application_type: Optional[Literal["交通費精算申請", "経費精算申請"]] = Field(None, description="確定した申請種別")
    application_form_name: Optional[str] = Field(None, description="申請書名")
    application_destination: Optional[str] = Field(None, description="申請先（要件上未定義）")
    judgment_basis: Optional[str] = Field(None, description="判断根拠")
    hitl_result: Optional[Literal["OK", "修正", "キャンセル"]] = Field(None, description="HitL承認結果")

    _validate_applicant_name = field_validator("applicant_name")(classmethod(_cls_validate_non_empty_string))
    _parse_application_date = field_validator("application_date", mode="before")(classmethod(_cls_parse_date))
    _normalize_hitl = field_validator("hitl_result", mode="before")(classmethod(_cls_normalize_hitl_result))
