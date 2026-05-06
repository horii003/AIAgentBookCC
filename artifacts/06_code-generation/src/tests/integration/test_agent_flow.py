# 参照: 結合テスト - モジュール連携動作検証
"""結合テスト

複数モジュールを組み合わせた連携動作を検証する。
外部API（LLM API等）への実際の呼び出しはモックを使用する。
"""
import sys
import os
import json
import tempfile
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestCalculateTransportFareIntegration:
    """calculate_transport_fare + FareCalculationInput の結合テスト"""

    def setup_method(self):
        """テスト用にモジュールレベルのデータをsrc/dataのファイルでリロードする。"""
        import tools.transport_tools as tt
        src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        train_path = os.path.join(src_dir, "data", "train_routes.json")
        fixed_path = os.path.join(src_dir, "data", "fixed_fares.json")

        if os.path.exists(train_path) and os.path.exists(fixed_path):
            result = tt.load_fare_data(train_path, fixed_path)
            if result[0]:
                tt._railway_routes, tt._fixed_fares = result[1]

    def test_validate_then_calculate_train(self):
        """FareCalculationInputのバリデーション後にcalculate_transport_fareが正しく運賃を返すこと。"""
        from models.data_models import FareCalculationInput
        from tools.transport_tools import calculate_transport_fare

        # バリデーション（BRL-14/BRL-15適用）
        validated = FareCalculationInput(
            departure="渋谷駅",  # 「駅」が除去されて「渋谷」になる
            destination="新宿駅",
            transport_type="JR",  # 「電車」に正規化される
        )
        assert validated.departure == "渋谷"
        assert validated.transport_type == "電車"

        # ツール実行（バリデーション済みの値を使用）
        ctx = MagicMock()
        ctx.invocation_state = {"applicant_name": "山田太郎", "application_date": "2026-05-06"}
        result = calculate_transport_fare(
            departure=validated.departure,
            destination=validated.destination,
            transport_type=validated.transport_type,
            tool_context=ctx,
        )
        assert result["success"] is True
        assert result["fare"] == 170

    def test_validate_then_calculate_bus(self):
        """バスでFareCalculationInputバリデーション後に固定運賃が返ること。"""
        from models.data_models import FareCalculationInput
        from tools.transport_tools import calculate_transport_fare

        validated = FareCalculationInput(
            departure="渋谷",
            destination="新宿",
            transport_type="路線バス",  # 「バス」に正規化
        )
        assert validated.transport_type == "バス"

        ctx = MagicMock()
        ctx.invocation_state = {}
        result = calculate_transport_fare(
            departure=validated.departure,
            destination=validated.destination,
            transport_type=validated.transport_type,
            tool_context=ctx,
        )
        assert result["success"] is True
        assert result["fare"] == 220


class TestGenerateTransportApplicationIntegration:
    """generate_transport_application + TransportApplicationData の結合テスト"""

    def test_validate_then_generate(self, tmp_path):
        """TransportApplicationDataバリデーション後にExcelファイルが生成されること。"""
        try:
            import openpyxl
        except ImportError:
            pytest.skip("openpyxl not available")

        from models.data_models import TransportApplicationData, TransportSegment

        # データバリデーション
        data = TransportApplicationData(
            applicant_name="山田太郎",
            application_date="2026-05-06",
            segments=[{
                "travel_date": "2026-05-01",
                "departure": "渋谷",
                "destination": "新宿",
                "transport_type": "電車",
                "fare": 170,
            }],
            purpose="取引先訪問",
        )
        assert data.applicant_name == "山田太郎"
        assert len(data.segments) == 1

        # Excelファイル生成
        template_path = tmp_path / "template.xlsx"
        wb = openpyxl.Workbook()
        wb.save(str(template_path))

        import tools.output_generator as og
        original_path = og.DATA_TRANSPORT_TEMPLATE_PATH
        original_output = og.OUTPUT_BASE_DIR
        original_audit = og.AUDIT_LOG_PATH

        try:
            og.DATA_TRANSPORT_TEMPLATE_PATH = str(template_path)
            og.OUTPUT_BASE_DIR = str(tmp_path / "output")
            og.AUDIT_LOG_PATH = str(tmp_path / "logs" / "audit.log")

            from tools.output_generator import generate_transport_application
            ctx = MagicMock()
            ctx.invocation_state = {
                "applicant_name": "山田太郎",
                "application_date": "2026-05-06",
                "session_id": "test_session",
            }
            result = generate_transport_application(
                segments=[{
                    "travel_date": "2026-05-01",
                    "departure": "渋谷",
                    "destination": "新宿",
                    "transport_type": "電車",
                    "fare": 170,
                }],
                purpose="取引先訪問",
                tool_context=ctx,
            )
            assert result["success"] is True
            assert os.path.exists(result["file_path"])
        finally:
            og.DATA_TRANSPORT_TEMPLATE_PATH = original_path
            og.OUTPUT_BASE_DIR = original_output
            og.AUDIT_LOG_PATH = original_audit


class TestGenerateExpenseApplicationIntegration:
    """generate_expense_application + ExpenseApplicationData の結合テスト"""

    def test_validate_then_generate(self, tmp_path):
        """ExpenseApplicationDataバリデーション後にExcelファイルが生成されること。"""
        try:
            import openpyxl
        except ImportError:
            pytest.skip("openpyxl not available")

        from models.data_models import ExpenseApplicationData

        # データバリデーション（BRL-12申請期限チェック含む）
        data = ExpenseApplicationData(
            applicant_name="山田太郎",
            application_date="2026-05-06",
            store_name="文具屋",
            expense_category="事務用品費",
            amount=1000,
            expense_date="2026-04-01",  # 35日差: OK
            purpose="業務用品購入",
        )
        assert data.expense_category == "事務用品費"

        # Excelファイル生成
        template_path = tmp_path / "expense_template.xlsx"
        wb = openpyxl.Workbook()
        wb.save(str(template_path))

        import tools.output_generator as og
        original_path = og.DATA_EXPENSE_TEMPLATE_PATH
        original_output = og.OUTPUT_BASE_DIR
        original_audit = og.AUDIT_LOG_PATH

        try:
            og.DATA_EXPENSE_TEMPLATE_PATH = str(template_path)
            og.OUTPUT_BASE_DIR = str(tmp_path / "output")
            og.AUDIT_LOG_PATH = str(tmp_path / "logs" / "audit.log")

            from tools.output_generator import generate_expense_application
            ctx = MagicMock()
            ctx.invocation_state = {
                "applicant_name": "山田太郎",
                "application_date": "2026-05-06",
                "session_id": "test_expense_session",
            }
            result = generate_expense_application(
                store_name="文具屋",
                expense_category="事務用品費",
                amount=1000,
                expense_date="2026-04-01",
                purpose="業務用品購入",
                tool_context=ctx,
            )
            assert result["success"] is True
            assert os.path.exists(result["file_path"])
        finally:
            og.DATA_EXPENSE_TEMPLATE_PATH = original_path
            og.OUTPUT_BASE_DIR = original_output
            og.AUDIT_LOG_PATH = original_audit


class TestHooksCombinedIntegration:
    """HumanApprovalHook + LoopControlHook の結合テスト"""

    def test_both_hooks_registered(self):
        """両フックが正常に登録できること（register_hooksが正常に動作すること）。"""
        from handlers.error_handler import HumanApprovalHook, LoopControlHook

        mock_registry = MagicMock()

        approval_hook = HumanApprovalHook()
        loop_hook = LoopControlHook(max_iterations=10, agent_name="test_agent")

        approval_hook.register_hooks(mock_registry)
        loop_hook.register_hooks(mock_registry)

        # 両方のフックがadd_callbackを呼び出していること
        assert mock_registry.add_callback.call_count >= 7  # 1 + 6

    def test_loop_control_counts_and_raises(self):
        """LoopControlHookが10回目でLoopLimitErrorを発生させること。"""
        from handlers.error_handler import LoopControlHook, LoopLimitError

        hook = LoopControlHook(max_iterations=10, agent_name="test_agent")

        event = MagicMock()
        event.exception = None

        # BeforeInvocationEventでリセット
        hook._before_invocation(MagicMock())
        assert hook.iteration_count == 0

        # 9回は継続
        for i in range(9):
            hook._after_model_call(event)
        assert hook.iteration_count == 9

        # 10回目でLoopLimitError
        with pytest.raises(LoopLimitError):
            hook._after_model_call(event)


class TestSessionManagerOrchestratorIntegration:
    """SessionManager + OrchestratorAgent の結合テスト"""

    def test_session_created_with_correct_id(self, tmp_path):
        """SessionManagerでセッションを作成後、OrchestratorAgentが同じsession_idを使用すること。"""
        with patch.dict("sys.modules", {
            "strands": MagicMock(),
            "strands.agent": MagicMock(),
            "strands.agent.conversation_manager": MagicMock(),
            "strands.exceptions": MagicMock(),
            "config.model_config": MagicMock(),
            "agents.transport_agent": MagicMock(),
            "agents.expense_agent": MagicMock(),
        }):
            if "agents.orchestrator_agent" in sys.modules:
                del sys.modules["agents.orchestrator_agent"]

            from agents.orchestrator_agent import OrchestratorAgent
            agent = OrchestratorAgent(applicant_name="山田太郎")

            # セッションIDが正しい形式であること
            assert "_" in agent._session_id

            # SessionManagerが同じsession_idを持つこと
            assert agent._session_manager.session_id == agent._session_id


class TestErrorHandlerValidationIntegration:
    """ErrorHandler + Pydanticモデルバリデーション の結合テスト"""

    def test_validation_error_message_generation(self):
        """実際のValidationErrorをErrorHandlerが適切なメッセージに変換すること。"""
        from models.data_models import FareCalculationInput
        from handlers.error_handler import ErrorHandler
        from pydantic import ValidationError

        handler = ErrorHandler()

        try:
            FareCalculationInput(
                departure="",
                destination="新宿",
                transport_type="電車",
            )
        except ValidationError as e:
            message = handler.handle_validation_error(e)
            assert isinstance(message, str)
            assert len(message) > 0

    def test_invalid_transport_validation_error(self):
        """無効な交通手段でValidationErrorが発生しErrorHandlerがメッセージを生成すること。"""
        from models.data_models import FareCalculationInput
        from handlers.error_handler import ErrorHandler
        from pydantic import ValidationError

        handler = ErrorHandler()

        try:
            FareCalculationInput(
                departure="渋谷",
                destination="新宿",
                transport_type="新幹線",
            )
        except ValidationError as e:
            message = handler.handle_validation_error(e)
            assert isinstance(message, str)
            assert len(message) > 0
