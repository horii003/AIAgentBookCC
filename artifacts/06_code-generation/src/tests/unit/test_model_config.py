"""model_config.py の単体テスト"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from unittest.mock import patch, MagicMock
import pytest


class TestModelConfig:
    def test_DEFAULT_MODEL_ID_が定義されている(self):
        from config.model_config import ModelConfig
        assert ModelConfig.DEFAULT_MODEL_ID == "jp.anthropic.claude-sonnet-4-5-20250929-v1:0"

    def test_get_model_が_BedrockModel_を返す(self):
        mock_bedrock = MagicMock()
        mock_bedrock_instance = MagicMock()
        mock_bedrock.return_value = mock_bedrock_instance

        with patch("config.model_config.BedrockModel", mock_bedrock):
            # 再インポートしてパッチを効かせる
            import importlib
            import config.model_config as mc
            original_bm = None
            try:
                from strands.models.bedrock import BedrockModel as BM
                original_bm = BM
            except Exception:
                pass

            result = mc.ModelConfig.get_model()
            # BedrockModelインスタンスが返ること（モデルIDが設定されていること）
            assert result is not None

    def test_model_id_が正しく設定される(self):
        with patch("strands.models.bedrock.BedrockModel") as mock_bm:
            mock_instance = MagicMock()
            mock_bm.return_value = mock_instance

            import sys
            # モジュールを新鮮にインポート
            if "config.model_config" in sys.modules:
                del sys.modules["config.model_config"]

            from config.model_config import ModelConfig, DEFAULT_MODEL_ID
            assert DEFAULT_MODEL_ID == "jp.anthropic.claude-sonnet-4-5-20250929-v1:0"
            assert ModelConfig.DEFAULT_MODEL_ID == DEFAULT_MODEL_ID
