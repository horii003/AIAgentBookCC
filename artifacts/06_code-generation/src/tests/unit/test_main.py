"""Unit tests for main.py"""
import sys
import pytest
from unittest.mock import MagicMock, patch


class TestMain:
    def test_import_succeeds(self):
        import main  # noqa: F401

    def test_fare_data_load_failure_causes_exit(self):
        import main

        with patch("tools.transport_tools._fare_loader") as mock_loader:
            mock_loader.load_train_routes.return_value = (False, "運賃データ読み込みエラー")
            with patch("builtins.print"):
                with pytest.raises(SystemExit) as exc_info:
                    main.main()
        assert exc_info.value.code == 1

    def test_fare_data_fixed_failure_causes_exit(self):
        import main

        with patch("tools.transport_tools._fare_loader") as mock_loader:
            mock_loader.load_train_routes.return_value = (True, "")
            mock_loader.load_fixed_fares.return_value = (False, "固定運賃データエラー")
            with patch("builtins.print"):
                with pytest.raises(SystemExit) as exc_info:
                    main.main()
        assert exc_info.value.code == 1

    def test_orchestrator_run_called(self):
        import main

        mock_app = MagicMock()

        with patch("tools.transport_tools._fare_loader") as mock_loader:
            mock_loader.load_train_routes.return_value = (True, "")
            mock_loader.load_fixed_fares.return_value = (True, "")
            with patch("agents.orchestrator_agent.OrchestratorApp", return_value=mock_app):
                main.main()

        mock_app.run.assert_called_once()

    def test_logging_configured(self):
        import logging
        root_logger = logging.getLogger()
        assert root_logger.handlers is not None
        assert len(root_logger.handlers) > 0
