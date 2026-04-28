"""main.py の単体テスト"""
import sys
import os
import unittest.mock as mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


class TestMain:
    def test_main_pyがimport可能である(self):
        import main
        assert main is not None

    def test_load_fare_data失敗時にsys_exitが呼ばれる(self):
        with mock.patch("main.load_dotenv"), \
             mock.patch("main._setup_logging"), \
             mock.patch("tools.travel_tools.load_fare_data", return_value=(False, "テストエラー")), \
             mock.patch("main.sys.exit", side_effect=SystemExit(1)) as mock_exit:
            import main as m
            try:
                m.main()
            except SystemExit:
                pass
            mock_exit.assert_called_once_with(1)

    def test_setup_loggingが正常に呼ばれる(self):
        with mock.patch("main.load_dotenv"), \
             mock.patch("main._setup_logging") as mock_setup, \
             mock.patch("tools.travel_tools.load_fare_data", return_value=(False, "err")), \
             mock.patch("main.sys.exit", side_effect=SystemExit(1)):
            import main as m
            try:
                m.main()
            except SystemExit:
                pass
            mock_setup.assert_called_once()
