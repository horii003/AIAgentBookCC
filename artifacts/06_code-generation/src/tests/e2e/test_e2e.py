"""E2Eテスト: main.py エントリーポイントの動作検証（モック使用）"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unittest.mock import MagicMock, patch


class TestE2EMainFlow:
    """main() の会話ループ動作を検証する。"""

    def _run_main(self, inputs, agent_response="申請を受け付けました"):
        mock_agent = MagicMock(return_value=agent_response)
        mock_session_manager = MagicMock()
        mock_session_manager.create_session.return_value = "sess_e2e"
        printed = []

        import main
        with patch("main.patch_human_approval_hook"), \
             patch("main.create_orchestrator_agent", return_value=mock_agent), \
             patch("main.SessionManagerFactory") as mock_factory, \
             patch("builtins.input", side_effect=inputs), \
             patch("builtins.print", side_effect=lambda *a, **kw: printed.append(" ".join(str(x) for x in a))):
            mock_factory.create.return_value = mock_session_manager
            main.main()

        return mock_agent, printed

    def test_welcome_message_displayed(self):
        mock_agent, printed = self._run_main(["田中太郎", "quit"])
        welcome = [p for p in printed if "ようこそ" in p]
        assert len(welcome) >= 1

    def test_valid_transport_request_calls_agent(self):
        mock_agent, _ = self._run_main(["田中太郎", "電車で新宿から渋谷に行きました", "quit"])
        mock_agent.assert_called_once()

    def test_valid_expense_request_calls_agent(self):
        mock_agent, _ = self._run_main(["田中太郎", "コンビニで事務用品を購入しました", "quit"])
        mock_agent.assert_called_once()

    def test_empty_input_does_not_call_agent(self):
        mock_agent, _ = self._run_main(["田中太郎", "", "quit"])
        mock_agent.assert_not_called()

    def test_oversized_input_does_not_call_agent(self):
        long_text = "あ" * 501
        mock_agent, _ = self._run_main(["田中太郎", long_text, "quit"])
        mock_agent.assert_not_called()

    def test_reset_command_prompts_for_new_name(self):
        mock_agent, _ = self._run_main(["田中太郎", "reset", "鈴木花子", "quit"])
        mock_agent.assert_not_called()

    def test_reset_command_in_japanese_works(self):
        mock_agent, _ = self._run_main(["田中太郎", "リセット", "鈴木花子", "quit"])
        mock_agent.assert_not_called()

    def test_agent_error_does_not_crash_loop(self):
        mock_agent = MagicMock(side_effect=[Exception("AWS error"), "recovery response"])
        mock_session_manager = MagicMock()
        mock_session_manager.create_session.return_value = "sess_e2e"

        import main
        with patch("main.patch_human_approval_hook"), \
             patch("main.create_orchestrator_agent", return_value=mock_agent), \
             patch("main.SessionManagerFactory") as mock_factory, \
             patch("builtins.input", side_effect=["田中太郎", "申請内容1", "申請内容2", "quit"]), \
             patch("builtins.print"):
            mock_factory.create.return_value = mock_session_manager
            main.main()

        assert mock_agent.call_count == 2
