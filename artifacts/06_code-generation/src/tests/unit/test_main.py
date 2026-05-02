import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unittest.mock import MagicMock, patch
import importlib


class TestMainModule:
    def test_import_ok(self):
        import main
        assert callable(main.main)

    def test_get_applicant_name_returns_stripped_input(self):
        import main
        with patch("builtins.input", return_value="  田中太郎  "):
            name = main._get_applicant_name()
        assert name == "田中太郎"

    def test_get_applicant_name_retries_on_empty(self):
        import main
        with patch("builtins.input", side_effect=["", "田中太郎"]):
            name = main._get_applicant_name()
        assert name == "田中太郎"

    def test_main_quit_exits_cleanly(self):
        import main
        mock_agent = MagicMock(return_value="response")
        mock_session_manager = MagicMock()
        mock_session_manager.create_session.return_value = "sess1"

        with patch("main.patch_human_approval_hook"), \
             patch("main.create_orchestrator_agent", return_value=mock_agent), \
             patch("main.SessionManagerFactory") as mock_factory, \
             patch("builtins.input", side_effect=["田中太郎", "quit"]), \
             patch("builtins.print"):
            mock_factory.create.return_value = mock_session_manager
            main.main()

        mock_agent.assert_not_called()

    def test_main_empty_input_skips_agent(self):
        import main
        mock_agent = MagicMock(return_value="response")
        mock_session_manager = MagicMock()
        mock_session_manager.create_session.return_value = "sess1"

        inputs = ["田中太郎", "", "quit"]
        with patch("main.patch_human_approval_hook"), \
             patch("main.create_orchestrator_agent", return_value=mock_agent), \
             patch("main.SessionManagerFactory") as mock_factory, \
             patch("builtins.input", side_effect=inputs), \
             patch("builtins.print"):
            mock_factory.create.return_value = mock_session_manager
            main.main()

        mock_agent.assert_not_called()

    def test_main_oversized_input_skips_agent(self):
        import main
        mock_agent = MagicMock(return_value="response")
        mock_session_manager = MagicMock()
        mock_session_manager.create_session.return_value = "sess1"

        long_input = "あ" * 501
        inputs = ["田中太郎", long_input, "quit"]
        with patch("main.patch_human_approval_hook"), \
             patch("main.create_orchestrator_agent", return_value=mock_agent), \
             patch("main.SessionManagerFactory") as mock_factory, \
             patch("builtins.input", side_effect=inputs), \
             patch("builtins.print"):
            mock_factory.create.return_value = mock_session_manager
            main.main()

        mock_agent.assert_not_called()

    def test_main_valid_input_calls_agent(self):
        import main
        mock_agent = MagicMock(return_value="申請を受け付けました")
        mock_session_manager = MagicMock()
        mock_session_manager.create_session.return_value = "sess1"

        inputs = ["田中太郎", "電車で渋谷から新宿", "quit"]
        with patch("main.patch_human_approval_hook"), \
             patch("main.create_orchestrator_agent", return_value=mock_agent), \
             patch("main.SessionManagerFactory") as mock_factory, \
             patch("builtins.input", side_effect=inputs), \
             patch("builtins.print"):
            mock_factory.create.return_value = mock_session_manager
            main.main()

        mock_agent.assert_called_once()

    def test_main_reset_command_creates_new_session(self):
        import main
        mock_agent = MagicMock(return_value="response")
        mock_session_manager = MagicMock()
        mock_session_manager.create_session.side_effect = ["sess1", "sess2"]

        inputs = ["田中太郎", "reset", "鈴木花子", "quit"]
        with patch("main.patch_human_approval_hook"), \
             patch("main.create_orchestrator_agent", return_value=mock_agent), \
             patch("main.SessionManagerFactory") as mock_factory, \
             patch("builtins.input", side_effect=inputs), \
             patch("builtins.print"):
            mock_factory.create.return_value = mock_session_manager
            main.main()

        assert mock_session_manager.create_session.call_count == 2

    def test_main_agent_exception_handled(self):
        import main
        mock_agent = MagicMock(side_effect=Exception("unexpected"))
        mock_session_manager = MagicMock()
        mock_session_manager.create_session.return_value = "sess1"

        inputs = ["田中太郎", "電車で出張", "quit"]
        with patch("main.patch_human_approval_hook"), \
             patch("main.create_orchestrator_agent", return_value=mock_agent), \
             patch("main.SessionManagerFactory") as mock_factory, \
             patch("builtins.input", side_effect=inputs), \
             patch("builtins.print"):
            mock_factory.create.return_value = mock_session_manager
            main.main()
