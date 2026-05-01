"""model_config.py の単体テスト"""
import os
import pytest
from unittest.mock import patch, MagicMock


class TestModelConfig:
    def test_get_model_returns_bedrock_model(self):
        """get_model() が BedrockModel を返すこと"""
        from config.model_config import ModelConfig
        with patch("config.model_config.BedrockModel") as mock_bedrock:
            mock_bedrock.return_value = MagicMock()
            model = ModelConfig.get_model()
            assert model is not None
            mock_bedrock.assert_called_once()

    def test_default_model_id(self):
        """DEFAULT_MODEL_ID が設定されていること"""
        from config.model_config import ModelConfig
        assert ModelConfig.DEFAULT_MODEL_ID == "jp.anthropic.claude-sonnet-4-5-20250929-v1:0"

    def test_guardrail_id_from_env(self):
        """環境変数 GUARDRAIL_ID が読み込まれること"""
        with patch.dict(os.environ, {"GUARDRAIL_ID": "test-guardrail-id"}):
            import importlib
            import config.model_config as mc
            importlib.reload(mc)
            assert mc.ModelConfig.GUARDRAIL_ID == "test-guardrail-id"

    def test_guardrail_version_from_env(self):
        """環境変数 GUARDRAIL_VERSION が読み込まれること"""
        with patch.dict(os.environ, {"GUARDRAIL_VERSION": "1"}):
            import importlib
            import config.model_config as mc
            importlib.reload(mc)
            assert mc.ModelConfig.GUARDRAIL_VERSION == "1"

    def test_guardrail_version_default(self):
        """GUARDRAIL_VERSION のデフォルト値が 'DRAFT' であること"""
        with patch.dict(os.environ, {}, clear=False):
            env = {k: v for k, v in os.environ.items() if k != "GUARDRAIL_VERSION"}
            with patch.dict(os.environ, env, clear=True):
                import importlib
                import config.model_config as mc
                importlib.reload(mc)
                assert mc.ModelConfig.GUARDRAIL_VERSION == "DRAFT"
