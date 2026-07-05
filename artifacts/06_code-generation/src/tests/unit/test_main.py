"""mainの単体テスト"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from unittest.mock import MagicMock, patch
import main as main_module


class TestMain:
    def test_KeyboardInterruptで正常終了する(self):
        mock_orchestrator = MagicMock()
        mock_orchestrator.run.side_effect = KeyboardInterrupt()

        with patch.object(main_module, "OrchestratorAgent", return_value=mock_orchestrator):
            with patch("builtins.print"):
                main_module.main()

    def test_Exceptionでsys_exitが呼ばれる(self):
        mock_orchestrator = MagicMock()
        mock_orchestrator.run.side_effect = RuntimeError("unexpected")

        with patch.object(main_module, "OrchestratorAgent", return_value=mock_orchestrator):
            with patch("builtins.print"):
                with pytest.raises(SystemExit) as exc_info:
                    main_module.main()
        assert exc_info.value.code == 1

    def test_正常終了時にsys_exitが呼ばれない(self):
        mock_orchestrator = MagicMock()
        mock_orchestrator.run.return_value = None

        with patch.object(main_module, "OrchestratorAgent", return_value=mock_orchestrator):
            main_module.main()

    def test_ログ設定にコンソールハンドラーがある(self):
        import logging
        root_logger = logging.getLogger()
        from logging.handlers import RotatingFileHandler
        handler_types = [type(h) for h in root_logger.handlers]
        assert logging.StreamHandler in handler_types or any(
            isinstance(h, logging.StreamHandler) for h in root_logger.handlers
        )
