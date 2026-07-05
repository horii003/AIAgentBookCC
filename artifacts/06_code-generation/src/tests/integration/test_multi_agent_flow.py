"""マルチエージェントフロー結合テスト

セッションマネージャ・フック・ツール・エージェント間の連携を検証する。
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from unittest.mock import MagicMock, patch, call

from handlers.error_handler import LoopLimitError, ErrorHandler
from handlers.human_approval_hook import HumanApprovalHook
from handlers.loop_control_hook import LoopControlHook
from session.session_manager import SessionManagerFactory
import tools.transport_tools as tt
from tools.transport_tools import calculate_transport_fare


class TestSessionManagerToAgentInit:
    """セッションID生成〜セッションマネージャ作成〜エージェント初期化の連携確認"""

    def test_session_idからエージェント初期化が完了する(self):
        session_id = SessionManagerFactory.generate_session_id()
        assert len(session_id) > 0

        with patch("session.session_manager.FileSessionManager") as mock_fsm:
            sm = SessionManagerFactory.create_session_manager(session_id)
            mock_fsm.assert_called_once_with(
                session_id=session_id,
                storage_dir=SessionManagerFactory.get_storage_dir(),
            )

    def test_プレフィックス付きsession_idが生成される(self):
        session_id = SessionManagerFactory.generate_session_id(prefix="test")
        assert session_id.startswith("test_")

    def test_異なるsession_idは一意である(self):
        ids = {SessionManagerFactory.generate_session_id() for _ in range(10)}
        assert len(ids) == 10


class TestTransportToolToFormGenerationFlow:
    """calculate_transport_fare → generate_transport_expense_form の連携フロー確認"""

    def setup_method(self):
        tt._train_fares_cache = {"渋谷": {"新宿": 200}}
        tt._fixed_fares_cache = {"バス": 230, "タクシー": 10000}

    def test_電車運賃計算結果が申請書生成ツールの入力として使える(self, tmp_path):
        fare_result = calculate_transport_fare(
            departure="渋谷",
            destination="新宿",
            transport_type="電車",
            travel_date="2026-07-03",
            purpose="取引先訪問",
        )
        assert "fare" in fare_result
        assert fare_result["fare"] == 200

        section = {
            "travel_date": fare_result["travel_date"],
            "departure": fare_result["departure"],
            "destination": fare_result["destination"],
            "transport_type": fare_result["transport_type"],
            "fare": fare_result["fare"],
            "purpose": "取引先訪問",
        }

        from tools.output_generator import generate_transport_expense_form

        ctx = MagicMock()
        ctx.invocation_state = {
            "applicant_name": "山田太郎",
            "application_date": "2026-07-03",
        }
        mock_wb = MagicMock()
        mock_wb.active = MagicMock()

        with patch("tools.output_generator.os.path.exists", return_value=True):
            with patch("tools.output_generator.openpyxl.load_workbook", return_value=mock_wb):
                with patch("tools.output_generator._OUTPUT_DIR", str(tmp_path)):
                    result = generate_transport_expense_form(
                        sections=[section],
                        total_fare=fare_result["fare"],
                        tool_context=ctx,
                    )

        assert result["status"] == "success"


class TestHumanApprovalHookCancelFlow:
    """HumanApprovalHook でのキャンセル時に申請書生成がスキップされること"""

    def test_CANCEL承認でcancel_toolがセットされる(self):
        def cancel_callback(tool_name, tool_params):
            return (False, "CANCEL")

        hook = HumanApprovalHook(approval_callback=cancel_callback)

        event = MagicMock()
        event.tool_use = {"name": "generate_transport_expense_form", "input": {}}
        event.cancel_tool = None

        hook._on_before_tool_call(event)

        assert event.cancel_tool is not None
        assert "キャンセル" in event.cancel_tool or "中止" in event.cancel_tool

    def test_承認対象外ツールはcancel_toolがセットされない(self):
        def deny_all(tool_name, tool_params):
            return (False, "CANCEL")

        hook = HumanApprovalHook(approval_callback=deny_all)

        event = MagicMock()
        event.tool_use = {"name": "calculate_transport_fare", "input": {}}
        event.cancel_tool = None

        hook._on_before_tool_call(event)

        assert event.cancel_tool is None


class TestLoopLimitErrorPropagation:
    """LoopLimitError が OrchestratorAgent.run() で適切にハンドリングされること"""

    def test_LoopControlHookがmax_iterations超過でLoopLimitErrorを発生させる(self):
        hook = LoopControlHook(max_iterations=2, agent_name="テストエージェント")

        class FakeEvent:
            exception = None

        event = FakeEvent()
        hook.iteration_count = 2

        with pytest.raises(LoopLimitError) as exc_info:
            hook.on_after_model_call(event)

        assert exc_info.value.agent_name == "テストエージェント"

    def test_OrchestratorAgentがLoopLimitErrorをハンドリングする(self):
        from agents.orchestrator_agent import OrchestratorAgent

        oa = OrchestratorAgent()
        mock_agent = MagicMock()
        mock_agent.side_effect = LoopLimitError(
            current_iteration=11, max_iterations=10, agent_name="reception_agent"
        )
        oa.agent = mock_agent
        oa._session_id = "20260703120000_abc12345"

        printed = []
        with patch("builtins.input", side_effect=["申請したい", "quit"]):
            with patch("builtins.print", side_effect=lambda *a: printed.append(str(a))):
                with patch("agents.orchestrator_agent.Agent", return_value=mock_agent):
                    with patch("agents.orchestrator_agent.SessionManagerFactory"):
                        with patch("agents.orchestrator_agent.ModelConfig"):
                            oa.run(MagicMock(), MagicMock())

        all_output = " ".join(printed)
        assert len(all_output) > 0


class TestInvocationStatePropagation:
    """invocation_state がオーケストレーターから専門エージェントへ正しく伝播すること"""

    def test_invoke_specialist_agentがapplicant_nameを伝播する(self):
        from agents.base_agent import invoke_specialist_agent

        ctx = MagicMock()
        ctx.invocation_state = {
            "applicant_name": "田中花子",
            "application_date": "2026-07-03",
            "session_id": "sess_test1234",
        }

        received_state = {}

        def capture_build(session_id, applicant_name, application_date, deadline):
            received_state["applicant_name"] = applicant_name
            received_state["application_date"] = application_date
            received_state["session_id"] = session_id
            mock = MagicMock()
            mock.return_value = "OK"
            return mock

        invoke_specialist_agent(
            query="申請",
            tool_context=ctx,
            agent_id="AG-002",
            deadline_months=3,
            build_agent=capture_build,
        )

        assert received_state["applicant_name"] == "田中花子"
        assert received_state["application_date"] == "2026-07-03"

    def test_子エージェントにsession_idが渡されない(self):
        from agents.base_agent import invoke_specialist_agent

        ctx = MagicMock()
        ctx.invocation_state = {
            "applicant_name": "田中花子",
            "application_date": "2026-07-03",
            "session_id": "sess_test1234",
        }

        child_invocation_state = {}

        def build_and_capture(session_id, applicant_name, application_date, deadline):
            mock = MagicMock()

            def capture_call(query, invocation_state=None):
                if invocation_state:
                    child_invocation_state.update(invocation_state)
                return "OK"

            mock.side_effect = capture_call
            return mock

        invoke_specialist_agent(
            query="申請",
            tool_context=ctx,
            agent_id="AG-002",
            deadline_months=3,
            build_agent=build_and_capture,
        )

        assert "session_id" not in child_invocation_state
        assert "applicant_name" in child_invocation_state
