"""データモデルの単体テスト"""
import sys
import os
from datetime import date
import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from models.data_models import (
    TransportSectionInput,
    TransportSection,
    TransportExpenseFormInput,
    ExpenseItem,
    GeneralExpenseFormInput,
    TransportFareOutput,
    ApplicationFormOutput,
    CollectedTransportInfo,
    CollectedExpenseInfo,
    SessionState,
    ApplicationContext,
    AgentDelegationMessage,
    validate_non_empty_string,
    parse_date,
    normalize_station_name,
    normalize_transport_type,
    parse_amount,
    normalize_expense_category,
    normalize_hitl_result,
)


# ============ 共通バリデーターのテスト ============

class TestValidateNonEmptyString:
    def test_正常な文字列(self):
        assert validate_non_empty_string("田中太郎") == "田中太郎"

    def test_空文字でValueError(self):
        with pytest.raises(ValueError, match="必須"):
            validate_non_empty_string("")

    def test_空白のみでValueError(self):
        with pytest.raises(ValueError, match="必須"):
            validate_non_empty_string("   ")

    def test_500文字は通過(self):
        assert validate_non_empty_string("a" * 500) == "a" * 500

    def test_501文字超でValueError(self):
        with pytest.raises(ValueError, match="長すぎます"):
            validate_non_empty_string("a" * 501)


class TestParseDate:
    def test_YYYY_MM_DD形式(self):
        assert parse_date("2026-07-03") == date(2026, 7, 3)

    def test_YYYY_MM_DD_スラッシュ形式(self):
        assert parse_date("2026/07/03") == date(2026, 7, 3)

    def test_date型はそのまま通過(self):
        d = date(2026, 7, 3)
        assert parse_date(d) == d

    def test_不正な形式でValueError(self):
        # dateutil が解釈できない完全な不正文字列でテスト（設計書：python-dateutil での解釈に依存）
        with pytest.raises(ValueError, match="日付の形式"):
            parse_date("abc-def-ghi")

    def test_無効な日付文字列でValueError(self):
        with pytest.raises(ValueError, match="日付の形式"):
            parse_date("not-a-date")


class TestNormalizeStationName:
    def test_駅サフィックス除去(self):
        assert normalize_station_name("渋谷駅") == "渋谷"

    def test_駅なしはそのまま(self):
        assert normalize_station_name("新宿") == "新宿"

    def test_駅のみでValueError(self):
        with pytest.raises(ValueError, match="駅名を入力"):
            normalize_station_name("駅")

    def test_空文字でValueError(self):
        with pytest.raises(ValueError, match="駅名を入力"):
            normalize_station_name("  ")


class TestNormalizeTransportType:
    def test_電車はそのまま(self):
        assert normalize_transport_type("電車") == "電車"

    def test_trainが電車に変換(self):
        assert normalize_transport_type("train") == "電車"

    def test_taxiがタクシーに変換(self):
        assert normalize_transport_type("taxi") == "タクシー"

    def test_busがバスに変換(self):
        assert normalize_transport_type("bus") == "バス"

    def test_planeが飛行機に変換(self):
        assert normalize_transport_type("plane") == "飛行機"

    def test_対象外でValueError(self):
        with pytest.raises(ValueError, match="交通手段は"):
            normalize_transport_type("自転車")


class TestParseAmount:
    def test_整数はそのまま(self):
        assert parse_amount(10000) == 10000

    def test_カンマ除去(self):
        assert parse_amount("10,000") == 10000

    def test_円除去(self):
        assert parse_amount("10000円") == 10000

    def test_カンマと円を除去(self):
        assert parse_amount("10,000円") == 10000

    def test_ゼロは通過(self):
        assert parse_amount(0) == 0

    def test_負数でValueError(self):
        with pytest.raises(ValueError, match="金額の形式"):
            parse_amount(-100)

    def test_文字列の負数でValueError(self):
        with pytest.raises(ValueError, match="金額の形式"):
            parse_amount("-100")

    def test_非数値文字列でValueError(self):
        with pytest.raises(ValueError, match="金額の形式"):
            parse_amount("abc")


class TestNormalizeExpenseCategory:
    def test_有効なカテゴリはそのまま(self):
        assert normalize_expense_category("事務用品費") == "事務用品費"

    def test_文房具が事務用品費に変換(self):
        assert normalize_expense_category("文房具") == "事務用品費"

    def test_宿泊が宿泊費に変換(self):
        assert normalize_expense_category("宿泊") == "宿泊費"

    def test_資格が資格精算費に変換(self):
        assert normalize_expense_category("資格") == "資格精算費"

    def test_不明なカテゴリはその他経費にフォールバック(self):
        # ValueError非送出
        result = normalize_expense_category("雑費")
        assert result == "その他経費"


# ============ TransportSectionInputのテスト ============

class TestTransportSectionInput:
    def _valid_data(self):
        return {
            "travel_date": "2026-07-03",
            "departure": "渋谷",
            "destination": "新宿",
            "transport_type": "電車",
            "purpose": "取引先訪問",
        }

    def test_正常インスタンス化(self):
        data = self._valid_data()
        obj = TransportSectionInput(**data)
        assert obj.travel_date == date(2026, 7, 3)
        assert obj.departure == "渋谷"

    def test_駅サフィックスが除去される(self):
        data = self._valid_data()
        data["departure"] = "渋谷駅"
        obj = TransportSectionInput(**data)
        assert obj.departure == "渋谷"

    def test_trainが電車に正規化される(self):
        data = self._valid_data()
        data["transport_type"] = "train"
        obj = TransportSectionInput(**data)
        assert obj.transport_type == "電車"

    def test_空の業務目的でValidationError(self):
        data = self._valid_data()
        data["purpose"] = ""
        with pytest.raises(ValidationError):
            TransportSectionInput(**data)

    def test_対象外の交通手段でValidationError(self):
        data = self._valid_data()
        data["transport_type"] = "自転車"
        with pytest.raises(ValidationError):
            TransportSectionInput(**data)


# ============ TransportExpenseFormInputのテスト ============

class TestTransportExpenseFormInput:
    def _valid_section(self):
        return TransportSection(
            travel_date="2026-07-03",
            departure="渋谷",
            destination="新宿",
            transport_type="電車",
            fare=200,
            purpose="取引先訪問",
        )

    def test_正常インスタンス化(self):
        obj = TransportExpenseFormInput(
            applicant_name="田中太郎",
            application_date="2026-07-03",
            sections=[self._valid_section()],
            total_fare=200,
        )
        assert obj.applicant_name == "田中太郎"
        assert len(obj.sections) == 1

    def test_セクション空リストでValidationError(self):
        with pytest.raises(ValidationError, match="1件以上"):
            TransportExpenseFormInput(
                applicant_name="田中太郎",
                application_date="2026-07-03",
                sections=[],
                total_fare=0,
            )


# ============ ExpenseItemのテスト ============

class TestExpenseItem:
    def _valid_data(self):
        return {
            "purchase_date": "2026-07-01",
            "store_name": "ヨドバシカメラ",
            "item_name": "ボールペン",
            "expense_category": "事務用品費",
            "amount": 500,
            "purpose": "業務用消耗品",
        }

    def test_正常インスタンス化(self):
        obj = ExpenseItem(**self._valid_data())
        assert obj.purchase_date == date(2026, 7, 1)
        assert obj.expense_category == "事務用品費"

    def test_文房具が事務用品費に正規化される(self):
        data = self._valid_data()
        data["expense_category"] = "文房具"
        obj = ExpenseItem(**data)
        assert obj.expense_category == "事務用品費"

    def test_不明なカテゴリはその他経費にフォールバック(self):
        data = self._valid_data()
        data["expense_category"] = "雑費"
        obj = ExpenseItem(**data)
        assert obj.expense_category == "その他経費"


# ============ SessionStateのテスト ============

class TestSessionState:
    def test_正常インスタンス化(self):
        obj = SessionState(session_id="sess_abc123")
        assert obj.session_id == "sess_abc123"
        assert obj.status == "READY"
        assert obj.iteration == 0

    def test_sess_プレフィックスなしでValidationError(self):
        with pytest.raises(ValidationError, match="sess_"):
            SessionState(session_id="abc123")

    def test_hitl_result_okが正規化される(self):
        obj = SessionState(session_id="sess_abc123", hitl_result="ok")
        assert obj.hitl_result == "OK"

    def test_hitl_result_Noneは通過(self):
        obj = SessionState(session_id="sess_abc123", hitl_result=None)
        assert obj.hitl_result is None

    def test_無効なhitl_resultでValidationError(self):
        with pytest.raises(ValidationError):
            SessionState(session_id="sess_abc123", hitl_result="yes please")

    def test_負のiterationでValidationError(self):
        with pytest.raises(ValidationError):
            SessionState(session_id="sess_abc123", iteration=-1)


# ============ CollectedTransportInfoのテスト ============

class TestCollectedTransportInfo:
    def _valid_section(self):
        return TransportSection(
            travel_date="2026-07-03",
            departure="渋谷",
            destination="新宿",
            transport_type="電車",
            fare=200,
            purpose="取引先訪問",
        )

    def test_正常インスタンス化(self):
        obj = CollectedTransportInfo(
            applicant_name="田中太郎",
            application_date="2026-07-03",
            sections=[self._valid_section()],
            total_fare=200,
        )
        assert len(obj.sections) == 1

    def test_セクション空でValidationError(self):
        with pytest.raises(ValidationError, match="1件以上"):
            CollectedTransportInfo(
                applicant_name="田中太郎",
                application_date="2026-07-03",
                sections=[],
                total_fare=0,
            )


# ============ シリアライズテスト ============

class TestSerialization:
    def test_TransportSection_model_dump_jsonで日付がISO形式(self):
        obj = TransportSection(
            travel_date="2026-07-03",
            departure="渋谷",
            destination="新宿",
            transport_type="電車",
            fare=200,
            purpose="取引先訪問",
        )
        json_str = obj.model_dump_json()
        assert "2026-07-03" in json_str

    def test_SessionState_hitl_result_Noneがnullとして出力(self):
        obj = SessionState(session_id="sess_abc123")
        json_str = obj.model_dump_json()
        assert "null" in json_str

    def test_SessionState_model_validate_jsonでデシリアライズ(self):
        obj = SessionState(session_id="sess_abc123", status="RUNNING", iteration=3)
        json_str = obj.model_dump_json()
        restored = SessionState.model_validate_json(json_str)
        assert restored.session_id == "sess_abc123"
        assert restored.status == "RUNNING"
        assert restored.iteration == 3
