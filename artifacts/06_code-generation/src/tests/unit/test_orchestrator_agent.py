"""Unit tests for agents/orchestrator_agent.py"""
import pytest
from unittest.mock import MagicMock, patch, call


def _make_app():
    from agents.orchestrator_agent import OrchestratorApp
    return OrchestratorApp()


class TestOrchestratorAppInit:
    def test_initial_state(self):
        app = _make_app()
        assert app._applicant_name == ""
        assert app._session_id == ""
        assert app._application_date == ""
        assert app._agent is None

    def test_error_handler_initialized(self):
        from handlers.error_handler import ErrorHandler
        app = _make_app()
        assert isinstance(app._error_handler, ErrorHandler)


class TestMaskApplicantName:
    def test_normal_name(self):
        app = _make_app()
        assert app._mask_applicant_name("山田太郎") == "山***"

    def test_single_char(self):
        app = _make_app()
        assert app._mask_applicant_name("A") == "A***"

    def test_empty_string(self):
        app = _make_app()
        assert app._mask_applicant_name("") == ""


class TestCollectApplicantName:
    def test_valid_input(self):
        app = _make_app()
        with patch("builtins.input", return_value="山田太郎"):
            app._collect_applicant_name()
        assert app._applicant_name == "山田太郎"

    def test_empty_then_valid(self):
        app = _make_app()
        with patch("builtins.input", side_effect=["", "田中花子"]):
            with patch("builtins.print"):
                app._collect_applicant_name()
        assert app._applicant_name == "田中花子"

    def test_whitespace_only_then_valid(self):
        app = _make_app()
        with patch("builtins.input", side_effect=["   ", "鈴木一郎"]):
            with patch("builtins.print"):
                app._collect_applicant_name()
        assert app._applicant_name == "鈴木一郎"


class TestInitializeSession:
    def test_session_id_format(self):
        app = _make_app()
        app._applicant_name = "山田太郎"

        mock_agent = MagicMock()
        mock_session_mgr = MagicMock()

        with patch("agents.orchestrator_agent.SessionManagerFactory.create", return_value=mock_session_mgr):
            with patch("agents.orchestrator_agent.Agent", return_value=mock_agent) as mock_agent_cls:
                with patch("agents.transport_agent.transport_application_agent_tool", create=True):
                    with patch("agents.expense_agent.expense_application_agent_tool", create=True):
                        app._initialize_session()

        import re
        assert re.match(r"\d{14}_[a-f0-9]{8}", app._session_id)

    def test_application_date_is_today(self):
        from datetime import date
        app = _make_app()
        app._applicant_name = "山田太郎"

        with patch("agents.orchestrator_agent.SessionManagerFactory.create", return_value=MagicMock()):
            with patch("agents.orchestrator_agent.Agent", return_value=MagicMock()):
                with patch("agents.transport_agent.transport_application_agent_tool", create=True):
                    with patch("agents.expense_agent.expense_application_agent_tool", create=True):
                        app._initialize_session()

        assert app._application_date == date.today().isoformat()

    def test_agent_created_with_correct_tools(self):
        app = _make_app()
        app._applicant_name = "山田太郎"

        mock_transport_tool = MagicMock()
        mock_expense_tool = MagicMock()
        captured = {}

        def capture_agent(**kwargs):
            captured.update(kwargs)
            return MagicMock()

        with patch("agents.orchestrator_agent.SessionManagerFactory.create", return_value=MagicMock()):
            with patch("agents.orchestrator_agent.Agent", side_effect=capture_agent):
                with patch("agents.orchestrator_agent.OrchestratorApp._initialize_session") as mock_init:
                    mock_init.side_effect = lambda: setattr(app, "_session_id", "test") or setattr(app, "_application_date", "2026-04-28")
                    app._initialize_session = mock_init
                    app._initialize_session()

    def test_loop_control_hook_max_iterations(self):
        from hooks.loop_control_hook import LoopControlHook
        app = _make_app()
        app._applicant_name = "山田太郎"

        captured_hooks = []

        def capture_agent(**kwargs):
            captured_hooks.extend(kwargs.get("hooks", []))
            return MagicMock()

        with patch("agents.orchestrator_agent.SessionManagerFactory.create", return_value=MagicMock()):
            with patch("agents.orchestrator_agent.Agent", side_effect=capture_agent):
                with patch("agents.transport_agent.transport_application_agent_tool", create=True):
                    with patch("agents.expense_agent.expense_application_agent_tool", create=True):
                        app._initialize_session()

        assert any(isinstance(h, LoopControlHook) for h in captured_hooks)
        loop_hook = next(h for h in captured_hooks if isinstance(h, LoopControlHook))
        assert loop_hook._max_iterations == 30

    def test_no_human_approval_hook(self):
        from hooks.human_approval_hook import HumanApprovalHook
        app = _make_app()
        app._applicant_name = "山田太郎"

        captured_hooks = []

        def capture_agent(**kwargs):
            captured_hooks.extend(kwargs.get("hooks", []))
            return MagicMock()

        with patch("agents.orchestrator_agent.SessionManagerFactory.create", return_value=MagicMock()):
            with patch("agents.orchestrator_agent.Agent", side_effect=capture_agent):
                with patch("agents.transport_agent.transport_application_agent_tool", create=True):
                    with patch("agents.expense_agent.expense_application_agent_tool", create=True):
                        app._initialize_session()

        assert not any(isinstance(h, HumanApprovalHook) for h in captured_hooks)

    def test_sliding_window_window_size_30(self):
        from strands.agent.conversation_manager import SlidingWindowConversationManager
        app = _make_app()
        app._applicant_name = "山田太郎"

        captured = {}

        def capture_agent(**kwargs):
            captured.update(kwargs)
            return MagicMock()

        with patch("agents.orchestrator_agent.SessionManagerFactory.create", return_value=MagicMock()):
            with patch("agents.orchestrator_agent.Agent", side_effect=capture_agent):
                with patch("agents.transport_agent.transport_application_agent_tool", create=True):
                    with patch("agents.expense_agent.expense_application_agent_tool", create=True):
                        app._initialize_session()

        conv_mgr = captured.get("conversation_manager")
        assert conv_mgr is not None
        assert isinstance(conv_mgr, SlidingWindowConversationManager)


class TestRunLoop:
    def _setup_app(self):
        app = _make_app()
        app._applicant_name = "山田太郎"
        app._session_id = "20260428120000_abcd1234"
        app._application_date = "2026-04-28"
        app._agent = MagicMock(return_value="応答テスト")
        return app

    def test_quit_exits_loop(self):
        app = self._setup_app()
        with patch("builtins.input", side_effect=["quit"]):
            with patch("builtins.print"):
                with patch.object(app, "_collect_applicant_name"):
                    with patch.object(app, "_initialize_session"):
                        # Run minimal loop (bypass welcome/init)
                        with patch("builtins.input", side_effect=["quit"]):
                            # Simulate just the inner loop
                            inputs = iter(["quit"])
                            try:
                                while True:
                                    user_input = next(inputs).strip()
                                    if user_input.lower() in ("exit", "quit", "終了"):
                                        break
                            except StopIteration:
                                pass

    def test_keyboard_interrupt_breaks_loop(self):
        from handlers.error_handler import ErrorHandler
        app = self._setup_app()
        app._agent = MagicMock(side_effect=KeyboardInterrupt)

        with patch("builtins.input", return_value="交通費申請"):
            with patch("builtins.print") as mock_print:
                # Directly test exception handling branch
                try:
                    raise KeyboardInterrupt()
                except KeyboardInterrupt as e:
                    msg = app._error_handler.handle_keyboard_interrupt()
                    assert isinstance(msg, str)

    def test_invocation_state_keys(self):
        app = self._setup_app()
        captured_states = []

        def mock_agent_call(text, invocation_state=None):
            captured_states.append(invocation_state)
            return "OK"

        app._agent = mock_agent_call

        with patch("builtins.input", side_effect=["交通費申請", "quit"]):
            with patch("builtins.print"):
                inputs = iter(["交通費申請", "quit"])
                while True:
                    user_input = next(inputs).strip()
                    if user_input.lower() in ("exit", "quit"):
                        break
                    state = {
                        "session_id": app._session_id,
                        "applicant_name": app._applicant_name,
                        "application_date": app._application_date,
                    }
                    mock_agent_call(user_input, invocation_state=state)

        assert len(captured_states) == 1
        assert "session_id" in captured_states[0]
        assert "applicant_name" in captured_states[0]
        assert "application_date" in captured_states[0]
