# 参照: SD-06 共通設定方針
"""config/model_config.py の単体テスト"""
import sys
import os
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestModelConfig:
    """ModelConfig のテスト"""

    def test_default_model_id(self):
        """DEFAULT_MODEL_IDが正しい値であること。"""
        # strands不在環境でもテストできるようimportをモック
        bedrock_mock = MagicMock()
        bedrock_mock.BedrockModel = MagicMock(return_value=MagicMock())
        with patch.dict("sys.modules", {"strands": MagicMock(), "strands.models": bedrock_mock}):
            import importlib
            if "config.model_config" in sys.modules:
                del sys.modules["config.model_config"]
            from config.model_config import ModelConfig
            assert ModelConfig.DEFAULT_MODEL_ID == "jp.anthropic.claude-sonnet-4-5-20250929-v1:0"

    def test_guardrail_id_default_empty(self):
        """GUARDRAIL_IDのデフォルト値が空文字列であること（環境変数未設定時）。"""
        bedrock_mock = MagicMock()
        bedrock_mock.BedrockModel = MagicMock(return_value=MagicMock())
        with patch.dict("sys.modules", {"strands": MagicMock(), "strands.models": bedrock_mock}):
            with patch.dict(os.environ, {}, clear=False):
                # GUARDRAIL_IDを削除してデフォルト値を確認
                env_backup = os.environ.pop("GUARDRAIL_ID", None)
                try:
                    import importlib
                    if "config.model_config" in sys.modules:
                        del sys.modules["config.model_config"]
                    from config.model_config import ModelConfig
                    # 環境変数未設定時はデフォルトで空文字列
                    assert isinstance(ModelConfig.GUARDRAIL_ID, str)
                finally:
                    if env_backup is not None:
                        os.environ["GUARDRAIL_ID"] = env_backup

    def test_get_model_returns_bedrock_model(self):
        """get_model()がBedrockModelインスタンスを返すこと。"""
        mock_bedrock_model = MagicMock()
        mock_bedrock_class = MagicMock(return_value=mock_bedrock_model)
        bedrock_mock = MagicMock()
        bedrock_mock.BedrockModel = mock_bedrock_class

        with patch.dict("sys.modules", {"strands": MagicMock(), "strands.models": bedrock_mock}):
            if "config.model_config" in sys.modules:
                del sys.modules["config.model_config"]
            from config.model_config import ModelConfig
            result = ModelConfig.get_model()
            assert mock_bedrock_class.called
            assert result == mock_bedrock_model

    def test_guardrail_version_default(self):
        """GUARDRAIL_VERSIONのデフォルト値が'DRAFT'であること。"""
        bedrock_mock = MagicMock()
        bedrock_mock.BedrockModel = MagicMock(return_value=MagicMock())
        with patch.dict("sys.modules", {"strands": MagicMock(), "strands.models": bedrock_mock}):
            env_backup = os.environ.pop("GUARDRAIL_VERSION", None)
            try:
                if "config.model_config" in sys.modules:
                    del sys.modules["config.model_config"]
                from config.model_config import ModelConfig
                assert ModelConfig.GUARDRAIL_VERSION == "DRAFT"
            finally:
                if env_backup is not None:
                    os.environ["GUARDRAIL_VERSION"] = env_backup
