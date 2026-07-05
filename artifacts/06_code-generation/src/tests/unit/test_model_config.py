"""ModelConfigの単体テスト"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unittest.mock import patch, MagicMock
from config.model_config import ModelConfig


class TestModelConfig:
    def test_DEFAULT_MODEL_IDが設定されている(self):
        assert ModelConfig.DEFAULT_MODEL_ID == "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

    def test_GUARDRAIL_IDがNone(self):
        assert ModelConfig.GUARDRAIL_ID is None

    def test_GUARDRAIL_VERSIONがDRAFT(self):
        assert ModelConfig.GUARDRAIL_VERSION == "DRAFT"

    def test_get_modelがBedrockModelを返す(self):
        with patch("config.model_config.BedrockModel") as mock_bedrock:
            mock_instance = MagicMock()
            mock_bedrock.return_value = mock_instance
            # キャッシュをリセットするためメソッドを直接テスト
            ModelConfig.get_model.cache_clear()
            result = ModelConfig.get_model()
            mock_bedrock.assert_called_once_with(model_id=ModelConfig.DEFAULT_MODEL_ID)
            ModelConfig.get_model.cache_clear()

    def test_get_modelがキャッシュを使用する(self):
        with patch("config.model_config.BedrockModel") as mock_bedrock:
            mock_bedrock.return_value = MagicMock()
            ModelConfig.get_model.cache_clear()
            result1 = ModelConfig.get_model()
            result2 = ModelConfig.get_model()
            assert mock_bedrock.call_count == 1
            ModelConfig.get_model.cache_clear()

    def test_GUARDRAIL_IDが設定された場合ガードレール付きモデルを返す(self):
        original_id = ModelConfig.GUARDRAIL_ID
        try:
            ModelConfig.GUARDRAIL_ID = "test-guardrail-id"
            with patch("config.model_config.BedrockModel") as mock_bedrock:
                mock_bedrock.return_value = MagicMock()
                ModelConfig.get_model.cache_clear()
                ModelConfig.get_model()
                mock_bedrock.assert_called_once_with(
                    model_id=ModelConfig.DEFAULT_MODEL_ID,
                    guardrail_id="test-guardrail-id",
                    guardrail_version="DRAFT",
                    guardrail_trace="enabled",
                )
                ModelConfig.get_model.cache_clear()
        finally:
            ModelConfig.GUARDRAIL_ID = original_id
