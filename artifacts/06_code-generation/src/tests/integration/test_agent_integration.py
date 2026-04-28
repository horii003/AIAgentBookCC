"""結合テスト: エージェント連携フロー"""
import sys
import os
import unittest.mock as mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


class TestLoadFareDataIntegration:
    def test_load_fare_dataが正常完了し運賃データが読み込まれる(self):
        import tools.travel_tools as tt
        tt._train_fares = []
        tt._fixed_fares = {}
        success, msg = tt.load_fare_data()
        assert success is True
        assert msg == ""
        assert len(tt._train_fares) > 0
        assert len(tt._fixed_fares) > 0

    def test_train_faresに正しいデータが含まれる(self):
        import tools.travel_tools as tt
        tt._train_fares = []
        tt._fixed_fares = {}
        tt.load_fare_data()
        departures = [r.departure for r in tt._train_fares]
        assert "東京" in departures or "渋谷" in departures

    def test_fixed_faresにバスタクシー飛行機が含まれる(self):
        import tools.travel_tools as tt
        tt._train_fares = []
        tt._fixed_fares = {}
        tt.load_fare_data()
        assert "バス" in tt._fixed_fares
        assert "タクシー" in tt._fixed_fares
        assert "飛行機" in tt._fixed_fares


class TestCalculateTravelExpenseIntegration:
    def setup_method(self):
        import tools.travel_tools as tt
        tt._train_fares = []
        tt._fixed_fares = {}
        tt.load_fare_data()

    def test_既存経路の運賃が正しく返る(self):
        from tools.travel_tools import calculate_travel_expense
        ctx = mock.MagicMock()
        ctx.invocation_state = {"session_id": "test"}
        result = calculate_travel_expense(
            travel_date="2026-04-28",
            departure="東京",
            destination="新宿",
            transport_type="電車",
            tool_context=ctx,
        )
        assert result["success"] is True
        assert result["fare"] > 0
        assert result["calculation_basis"] == "電車経路テーブル参照"

    def test_バスの固定運賃が返る(self):
        from tools.travel_tools import calculate_travel_expense
        ctx = mock.MagicMock()
        ctx.invocation_state = {"session_id": "test"}
        result = calculate_travel_expense(
            travel_date="2026-04-28",
            departure="A",
            destination="B",
            transport_type="バス",
            tool_context=ctx,
        )
        assert result["success"] is True
        assert result["fare"] == 230


class TestGenerateTravelExpenseFormIntegration:
    def test_交通費精算申請書のxlsxが生成される(self):
        from tools.output_generator import generate_travel_expense_form
        ctx = mock.MagicMock()
        ctx.invocation_state = {
            "session_id": "integration_test_001",
            "applicant_name": "田中太郎",
            "application_date": "2026-04-28",
        }
        result = generate_travel_expense_form(
            items=[
                {
                    "travel_date": "2026-04-28",
                    "departure": "東京",
                    "destination": "新宿",
                    "transport_type": "電車",
                    "amount": 200,
                }
            ],
            business_purpose="社内会議",
            tool_context=ctx,
        )
        assert result["success"] is True
        assert os.path.exists(result["file_path"])
        assert result["file_path"].endswith(".xlsx")
        assert "交通費精算申請書" in result["file_path"]

    def test_経費精算申請書のxlsxが生成される(self):
        from tools.output_generator import generate_expense_form
        ctx = mock.MagicMock()
        ctx.invocation_state = {
            "session_id": "integration_test_002",
            "applicant_name": "田中太郎",
            "application_date": "2026-04-28",
        }
        result = generate_expense_form(
            items=[
                {
                    "purchase_date": "2026-04-28",
                    "store_name": "書店",
                    "item_name": "技術書",
                    "expense_category": "事務用品費",
                    "amount": 3000,
                }
            ],
            business_purpose="業務研究",
            tool_context=ctx,
        )
        assert result["success"] is True
        assert os.path.exists(result["file_path"])
        assert "経費精算申請書" in result["file_path"]


class TestHumanApprovalHookIntegration:
    def test_ok入力でevent_cancel_toolが設定されない(self):
        from handlers.hooks import HumanApprovalHook
        hook = HumanApprovalHook()
        event = mock.MagicMock()
        event.tool_name = "generate_travel_expense_form"
        event.tool_params = {}

        with mock.patch("builtins.input", return_value="ok"):
            result = hook._request_approval("generate_travel_expense_form", {})
        assert result == (True, "")

    def test_キャンセル入力でevent_cancel_toolが設定される(self):
        from handlers.hooks import HumanApprovalHook
        hook = HumanApprovalHook()

        with mock.patch("builtins.input", return_value="キャンセル"):
            result = hook._request_approval("generate_travel_expense_form", {})
        assert result == (False, "CANCEL")

    def test_非対象ツールではevent_cancel_toolが設定されない(self):
        from handlers.hooks import HumanApprovalHook
        hook = HumanApprovalHook()
        event = mock.MagicMock()
        event.tool_name = "calculate_travel_expense"
        event.tool_params = {}
        del event.cancel_tool
        hook._handle_before_tool_call(event)
        assert not hasattr(event, "cancel_tool") or event.cancel_tool != "申請をキャンセルしました。"


class TestLoopControlHookIntegration:
    def test_max_iterations超過時にLoopLimitErrorが送出される(self):
        from handlers.hooks import LoopControlHook
        from handlers.exceptions import LoopLimitError
        hook = LoopControlHook(max_iterations=3)
        import pytest
        with pytest.raises(LoopLimitError):
            for _ in range(4):
                hook._increment_and_check("test_agent")


class TestErrorHandlerIntegration:
    def test_handle_loop_limit_errorが正しいメッセージを返す(self):
        from handlers.error_handler import ErrorHandler
        from handlers.exceptions import LoopLimitError
        handler = ErrorHandler()
        e = LoopLimitError(5, 10, "test_agent")
        msg = handler.handle_loop_limit_error(e)
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_handle_unexpected_errorが正しいメッセージを返す(self):
        from handlers.error_handler import ErrorHandler
        handler = ErrorHandler()
        msg = handler.handle_unexpected_error(Exception("test"))
        assert "予期しないエラー" in msg or len(msg) > 0


class TestInvocationStateIntegration:
    def test_invocation_stateがTOOL001でToolContext経由で取得できる(self):
        import tools.travel_tools as tt
        tt._train_fares = []
        tt._fixed_fares = {}
        tt.load_fare_data()

        ctx = mock.MagicMock()
        ctx.invocation_state = {
            "session_id": "test_session_abc",
            "applicant_name": "鈴木花子",
            "application_date": "2026-04-28",
        }
        from tools.travel_tools import calculate_travel_expense
        result = calculate_travel_expense(
            travel_date="2026-04-28",
            departure="東京",
            destination="品川",
            transport_type="電車",
            tool_context=ctx,
        )
        assert result["success"] is True

    def test_invocation_stateがTOOL002でToolContext経由で取得できる(self):
        ctx = mock.MagicMock()
        ctx.invocation_state = {
            "session_id": "test_session_xyz",
            "applicant_name": "山田一郎",
            "application_date": "2026-04-28",
        }
        from tools.output_generator import generate_travel_expense_form
        result = generate_travel_expense_form(
            items=[{
                "travel_date": "2026-04-28",
                "departure": "東京",
                "destination": "品川",
                "transport_type": "電車",
                "amount": 170,
            }],
            business_purpose="外出",
            tool_context=ctx,
        )
        assert result["success"] is True
        assert "mountain_one_xyx" not in result["file_path"]
        assert "test_session_xyz" in result["file_path"]
