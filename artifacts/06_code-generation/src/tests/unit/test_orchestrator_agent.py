# 参照: DD-02a 申請受付窓口エージェント詳細設計書
"""agents/orchestrator_agent.py の単体テスト"""
import sys
import os
import re
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestOrchestratorAgent:
    """OrchestratorAgent の単体テスト"""

    def setup_method(self):
        """各テスト前のセットアップ（Agentのモック）。"""
        # strands未インストール時もテスト可能にする
        pass

    def _create_agent(self, applicant_name="山田太郎"):
        """テスト用OrchestratorAgentインスタンスを生成する。"""
        # strands依存をモック
        with patch.dict("sys.modules", {
            "strands": MagicMock(),
            "strands.agent": MagicMock(),
            "strands.agent.conversation_manager": MagicMock(),
            "strands.exceptions": MagicMock(),
            "config.model_config": MagicMock(),
            "agents.transport_agent": MagicMock(),
            "agents.expense_agent": MagicMock(),
        }):
            if "agents.orchestrator_agent" in sys.modules:
                del sys.modules["agents.orchestrator_agent"]
            from agents.orchestrator_agent import OrchestratorAgent
            agent = OrchestratorAgent(applicant_name=applicant_name)
        return agent

    def test_validate_input_empty(self):
        """_validate_input("")がエラーメッセージを返すこと。"""
        agent = self._create_agent()
        result = agent._validate_input("")
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    def test_validate_input_whitespace_only(self):
        """_validate_input("   ")がエラーメッセージを返すこと。"""
        agent = self._create_agent()
        result = agent._validate_input("   ")
        assert result is not None

    def test_validate_input_501_chars(self):
        """_validate_input("a" * 501)がエラーメッセージを返すこと（GRD-012）。"""
        agent = self._create_agent()
        result = agent._validate_input("a" * 501)
        assert result is not None
        assert isinstance(result, str)
        assert "500" in result

    def test_validate_input_normal(self):
        """_validate_input("正常な入力")がNoneを返すこと。"""
        agent = self._create_agent()
        result = agent._validate_input("タクシー代を精算したい")
        assert result is None

    def test_validate_input_500_chars(self):
        """_validate_input("a" * 500)がNoneを返すこと（境界値テスト）。"""
        agent = self._create_agent()
        result = agent._validate_input("a" * 500)
        assert result is None

    def test_get_invocation_state_keys(self):
        """_get_invocation_state()がapplicant_name/application_date/session_idを含む辞書を返すこと。"""
        agent = self._create_agent("山田太郎")
        state = agent._get_invocation_state()
        assert "applicant_name" in state
        assert "application_date" in state
        assert "session_id" in state
        assert state["applicant_name"] == "山田太郎"

    def test_session_id_format(self):
        """セッションIDが{タイムスタンプ}_{UUID8文字}形式であること。"""
        agent = self._create_agent()
        session_id = agent._session_id
        # 形式: YYYYMMDDHHMMSS_xxxxxxxx（14文字 + "_" + 8文字）
        pattern = r"^\d{14}_[0-9a-f]{8}$"
        assert re.match(pattern, session_id), f"Invalid session_id format: {session_id}"

    def test_applicant_name_stored(self):
        """初期化時にapplicant_nameが正しく保存されること。"""
        agent = self._create_agent("テスト申請者")
        assert agent._applicant_name == "テスト申請者"
