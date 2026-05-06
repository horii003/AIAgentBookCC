# 参照: DD-02a 申請受付窓口エージェント詳細設計書, SD-06 共通設定方針
"""main.py の単体テスト"""
import sys
import os
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestMain:
    """main.py の単体テスト"""

    def test_main_calls_orchestrator_agent(self):
        """main()がOrchestratorAgentを生成してrun()を呼び出すこと。"""
        mock_agent_instance = MagicMock()
        mock_orchestrator_class = MagicMock(return_value=mock_agent_instance)

        with patch("sys.argv", ["main.py", "山田太郎"]):
            with patch.dict("sys.modules", {
                "agents.orchestrator_agent": MagicMock(OrchestratorAgent=mock_orchestrator_class),
            }):
                if "main" in sys.modules:
                    del sys.modules["main"]
                import main as m
                m.main()

        mock_orchestrator_class.assert_called_once_with(applicant_name="山田太郎")
        mock_agent_instance.run.assert_called_once()

    def test_main_without_args_uses_input(self, monkeypatch):
        """main()が引数なしの場合input()で申請者名を取得すること。"""
        mock_agent_instance = MagicMock()
        mock_orchestrator_class = MagicMock(return_value=mock_agent_instance)

        monkeypatch.setattr("builtins.input", lambda _: "鈴木花子")

        with patch("sys.argv", ["main.py"]):
            with patch.dict("sys.modules", {
                "agents.orchestrator_agent": MagicMock(OrchestratorAgent=mock_orchestrator_class),
            }):
                if "main" in sys.modules:
                    del sys.modules["main"]
                import main as m
                m.main()

        mock_orchestrator_class.assert_called_once_with(applicant_name="鈴木花子")

    def test_main_empty_applicant_name_exits(self, monkeypatch):
        """main()で申請者名が空の場合に終了すること。"""
        monkeypatch.setattr("builtins.input", lambda _: "")

        with patch("sys.argv", ["main.py"]):
            with patch.dict("sys.modules", {
                "agents.orchestrator_agent": MagicMock(),
            }):
                if "main" in sys.modules:
                    del sys.modules["main"]
                import main as m
                # 空文字の場合はOrchestratorAgentが生成されずに終了する
                m.main()  # 例外が発生しないこと
