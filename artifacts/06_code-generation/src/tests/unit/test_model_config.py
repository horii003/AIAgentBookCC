"""Unit tests for config/model_config.py"""
from unittest.mock import patch, MagicMock

import pytest

from config.model_config import ModelConfig, DEFAULT_MODEL_ID


class TestModelConfig:
    def test_get_model_returns_bedrock_model(self):
        from strands.models import BedrockModel
        with patch("config.model_config.BedrockModel") as MockBedrock:
            mock_instance = MagicMock(spec=BedrockModel)
            MockBedrock.return_value = mock_instance
            result = ModelConfig.get_model()
            assert result is mock_instance

    def test_get_model_uses_default_model_id(self):
        with patch("config.model_config.BedrockModel") as MockBedrock:
            ModelConfig.get_model()
            MockBedrock.assert_called_once_with(model_id=DEFAULT_MODEL_ID)

    def test_default_model_id_value(self):
        assert DEFAULT_MODEL_ID == "jp.anthropic.claude-sonnet-4-5-20250929-v1:0"

    def test_class_default_model_id(self):
        assert ModelConfig.DEFAULT_MODEL_ID == DEFAULT_MODEL_ID

    def test_get_retry_strategy_returns_correct_type(self):
        from strands import ModelRetryStrategy
        strategy = ModelConfig.get_retry_strategy()
        assert isinstance(strategy, ModelRetryStrategy)

    def test_get_retry_strategy_max_attempts(self):
        strategy = ModelConfig.get_retry_strategy()
        assert strategy._max_attempts == 6

    def test_get_retry_strategy_initial_delay(self):
        strategy = ModelConfig.get_retry_strategy()
        assert strategy._initial_delay == 4

    def test_get_retry_strategy_max_delay(self):
        strategy = ModelConfig.get_retry_strategy()
        assert strategy._max_delay == 240
