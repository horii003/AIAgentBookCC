"""main.py の単体テスト"""
import pytest
from unittest.mock import patch, MagicMock, call


class TestMain:
    def test_main_calls_orchestrator_run(self):
        """main() が agents.orchestrator_agent.run() を呼び出すこと"""
        with patch("agents.orchestrator_agent.run") as mock_run, \
             patch("main.load_dotenv"):
            from main import main
            main()
        mock_run.assert_called_once()

    def test_main_handles_keyboard_interrupt(self, capsys):
        """main() で KeyboardInterrupt が発生してもクラッシュしないこと"""
        with patch("agents.orchestrator_agent.run", side_effect=KeyboardInterrupt()), \
             patch("main.load_dotenv"):
            from main import main
            main()
        captured = capsys.readouterr()
        assert "終了" in captured.out

    def test_main_handles_unexpected_exception(self):
        """main() で想定外 Exception が発生したとき sys.exit(1) が呼ばれること"""
        with patch("agents.orchestrator_agent.run", side_effect=Exception("テストエラー")), \
             patch("main.load_dotenv"), \
             pytest.raises(SystemExit) as exc_info:
            from main import main
            main()
        assert exc_info.value.code == 1
