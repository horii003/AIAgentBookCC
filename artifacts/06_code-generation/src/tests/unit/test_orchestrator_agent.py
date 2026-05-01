"""orchestrator_agent.py の単体テスト"""
import re
import pytest
from unittest.mock import patch, MagicMock

from agents.orchestrator_agent import (
    _generate_session_id,
    _create_ag001_agent,
    _run_repl,
    RESET_COMMANDS,
    EXIT_COMMANDS,
)


class TestGenerateSessionId:
    def test_session_id_format(self):
        """session_id が タイムスタンプ_UUID8 形式で生成されること"""
        session_id = _generate_session_id()
        pattern = r"^\d{14}_[0-9a-f]{8}$"
        assert re.match(pattern, session_id), f"形式不一致: {session_id}"

    def test_session_ids_are_unique(self):
        """2回生成した session_id が異なること"""
        id1 = _generate_session_id()
        id2 = _generate_session_id()
        assert id1 != id2


class TestCreateAg001Agent:
    def test_returns_agent_instance(self):
        """_create_ag001_agent が Agent インスタンスを返すこと"""
        from strands import Agent
        with patch("agents.orchestrator_agent.SessionManagerFactory.create"), \
             patch("agents.orchestrator_agent.ModelConfig.get_model"):
            agent = _create_ag001_agent("test-session-001")
        assert isinstance(agent, Agent)


class TestRunRepl:
    def test_exit_command_breaks_loop(self):
        """'exit' コマンドでループが終了すること"""
        mock_agent = MagicMock()
        with patch("builtins.input", side_effect=["exit"]):
            _run_repl(mock_agent, "test-session-001")
        mock_agent.assert_not_called()

    def test_quit_command_breaks_loop(self):
        """'quit' コマンドでループが終了すること"""
        mock_agent = MagicMock()
        with patch("builtins.input", side_effect=["quit"]):
            _run_repl(mock_agent, "test-session-001")
        mock_agent.assert_not_called()

    def test_reset_command_returns_none(self):
        """'reset' コマンドで None が返却されること"""
        mock_agent = MagicMock()
        with patch("builtins.input", side_effect=["reset"]):
            result = _run_repl(mock_agent, "test-session-001")
        assert result is None

    def test_input_exceeding_500_chars_shows_error(self, capsys):
        """501文字以上の入力でエラーメッセージが表示されること"""
        long_input = "あ" * 501
        mock_agent = MagicMock()
        with patch("builtins.input", side_effect=[long_input, "exit"]):
            _run_repl(mock_agent, "test-session-001")
        captured = capsys.readouterr()
        assert "500文字" in captured.out
        mock_agent.assert_not_called()

    def test_normal_input_calls_agent(self):
        """通常の入力でエージェントが呼び出されること"""
        mock_agent = MagicMock(return_value="エージェントの応答")
        with patch("builtins.input", side_effect=["交通費を申請したい", "exit"]):
            _run_repl(mock_agent, "test-session-001")
        mock_agent.assert_called_once()

    def test_keyboard_interrupt_breaks_loop(self):
        """KeyboardInterrupt でループが終了すること"""
        mock_agent = MagicMock()
        with patch("builtins.input", side_effect=KeyboardInterrupt()):
            _run_repl(mock_agent, "test-session-001")
        mock_agent.assert_not_called()

    def test_loop_limit_error_continues(self, capsys):
        """LoopLimitError 発生時にループが継続されること（break しないこと）"""
        from handlers.loop_control_hook import LoopLimitError

        call_count = 0

        def mock_agent(user_input, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise LoopLimitError(
                    current_iteration=10,
                    max_iterations=10,
                    agent_name="AG-001",
                )
            return "正常応答"

        with patch("builtins.input", side_effect=["入力1", "入力2", "exit"]):
            _run_repl(mock_agent, "test-session-001")

        assert call_count == 2

    def test_invocation_state_contains_application_date(self):
        """invocation_state に application_date が設定されること"""
        captured_state = {}

        def mock_agent(user_input, **kwargs):
            captured_state.update(kwargs.get("invocation_state", {}))
            return "応答"

        with patch("builtins.input", side_effect=["テスト入力", "exit"]):
            _run_repl(mock_agent, "test-session-001")

        assert "application_date" in captured_state
        import re
        assert re.match(r"\d{4}-\d{2}-\d{2}", captured_state["application_date"])
