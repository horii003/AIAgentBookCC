"""結合テスト: 申請フロー全体の連携動作を検証する"""
import re
import pytest
from unittest.mock import patch, MagicMock


class TestOrchestratorSessionId:
    def test_session_id_format_on_init(self):
        """Orchestrator 初期化時に session_id が正しい形式で生成されること"""
        from agents.orchestrator_agent import _generate_session_id
        session_id = _generate_session_id()
        pattern = r"^\d{14}_[0-9a-f]{8}$"
        assert re.match(pattern, session_id)


class TestTransportAgentToolFunction:
    def setup_method(self):
        from agents.transport_agent import _agent_instances
        _agent_instances.clear()

    def test_transport_agent_returns_str_response(self):
        """transport_agent ツール関数がモック環境で str 応答を返すこと"""
        from agents.transport_agent import handle_transport_expense_application
        from strands.types.tools import ToolContext

        ctx = MagicMock(spec=ToolContext)
        ctx.invocation_state = {
            "session_id": "integration-test-001",
            "applicant_name": "テスト太郎",
            "application_date": "2026-05-01",
        }

        mock_agent = MagicMock(return_value="交通費精算申請書を生成しました。")

        with patch("agents.transport_agent.Agent", return_value=mock_agent), \
             patch("agents.transport_agent.SessionManagerFactory.create"), \
             patch("agents.transport_agent.ModelConfig.get_model"):
            result = handle_transport_expense_application("交通費申請をお願いします", ctx)

        assert isinstance(result, str)


class TestExpenseAgentToolFunction:
    def setup_method(self):
        from agents.expense_agent import _agent_instances
        _agent_instances.clear()

    def test_expense_agent_returns_str_response(self):
        """expense_agent ツール関数がモック環境で str 応答を返すこと"""
        from agents.expense_agent import handle_expense_application
        from strands.types.tools import ToolContext

        ctx = MagicMock(spec=ToolContext)
        ctx.invocation_state = {
            "session_id": "integration-test-002",
            "applicant_name": "テスト花子",
            "application_date": "2026-05-01",
        }

        mock_agent = MagicMock(return_value="経費精算申請書を生成しました。")

        with patch("agents.expense_agent.Agent", return_value=mock_agent), \
             patch("agents.expense_agent.SessionManagerFactory.create"), \
             patch("agents.expense_agent.ModelConfig.get_model"):
            result = handle_expense_application("経費申請をお願いします", ctx)

        assert isinstance(result, str)


class TestInvocationStatePropagation:
    def setup_method(self):
        from agents.transport_agent import _agent_instances
        _agent_instances.clear()

    def test_invocation_state_propagated_to_transport_agent(self):
        """invocation_state の applicant_name・application_date が AG-002 へ正しく伝播すること"""
        from agents.transport_agent import handle_transport_expense_application
        from strands.types.tools import ToolContext

        ctx = MagicMock(spec=ToolContext)
        ctx.invocation_state = {
            "session_id": "propagation-test-001",
            "applicant_name": "伝播テスト",
            "application_date": "2026-04-01",
        }

        captured_state = {}
        mock_agent_instance = MagicMock()

        def mock_call(*args, **kwargs):
            captured_state.update(kwargs.get("invocation_state", {}))
            return "応答"

        mock_agent_instance.side_effect = mock_call

        with patch("agents.transport_agent.Agent", return_value=mock_agent_instance), \
             patch("agents.transport_agent.SessionManagerFactory.create"), \
             patch("agents.transport_agent.ModelConfig.get_model"):
            handle_transport_expense_application("テストクエリ", ctx)

        assert captured_state.get("applicant_name") == "伝播テスト"
        assert captured_state.get("application_date") == "2026-04-01"
        assert captured_state.get("session_id") == "propagation-test-001"


class TestLoopLimitErrorHandling:
    def setup_method(self):
        from agents.transport_agent import _agent_instances
        _agent_instances.clear()

    def test_loop_limit_error_in_orchestrator_continues_loop(self):
        """Orchestrator で LoopLimitError 発生時に対話ループが継続すること"""
        from agents.orchestrator_agent import _run_repl
        from handlers.error_handler import LoopLimitError

        call_count = 0

        def mock_agent_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise LoopLimitError(
                    current_iteration=30,
                    max_iterations=30,
                    agent_name="AG-001",
                )
            return "正常応答"

        mock_agent = MagicMock(side_effect=mock_agent_call)

        with patch("builtins.input", side_effect=["入力1", "入力2", "exit"]):
            _run_repl(mock_agent, "loop-test-session")

        assert call_count == 2


class TestTransportCalculatorWithFareData:
    def test_calculate_transport_fare_with_real_data(self):
        """train_routes.json を使った calculate_transport_fare が正しく動作すること"""
        import json
        import os

        train_routes_path = "data/train_routes.json"
        if not os.path.exists(train_routes_path):
            pytest.skip("train_routes.json が見つかりません")

        with open(train_routes_path, encoding="utf-8") as f:
            data = json.load(f)

        routes = data.get("routes", [])
        if not routes:
            pytest.skip("train_routes.json にルートデータがありません")

        first_route = routes[0]
        from_station = first_route["from"]
        to_station = first_route["to"]
        expected_fare = first_route["fare"]

        from tools.transport_calculator import calculate_transport_fare
        result = calculate_transport_fare("電車", from_station, to_station, "2026-05-01")

        assert result["success"] is True
        assert result["calculable"] is True
        assert result["fare"] == expected_fare


class TestApplicationGeneratorCellMapping:
    def test_transport_application_writes_to_correct_cells(self):
        """generate_transport_application が指定セル位置に正しく書き込むこと"""
        from tools.application_generator import generate_transport_application
        from strands.types.tools import ToolContext

        ctx = MagicMock(spec=ToolContext)
        ctx.invocation_state = {
            "applicant_name": "セルテスト太郎",
            "application_date": "2026-05-01",
            "session_id": "cell-test-session",
        }

        collected_items = {
            "segments": [
                {
                    "travel_date": "2026-04-15",
                    "departure": "渋谷",
                    "destination": "品川",
                    "transport_type": "電車",
                    "fare": 250,
                    "business_purpose": "顧客訪問",
                }
            ]
        }

        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws

        with patch("os.path.exists", return_value=True), \
             patch("openpyxl.load_workbook", return_value=mock_wb), \
             patch("os.makedirs"), \
             patch.object(mock_wb, "save"):
            result = generate_transport_application(collected_items, ctx)

        assert result["success"] is True
        mock_ws.__setitem__.assert_any_call("B3", "セルテスト太郎")
        mock_ws.__setitem__.assert_any_call("A7", 1)
        mock_ws.__setitem__.assert_any_call("F7", 250)
