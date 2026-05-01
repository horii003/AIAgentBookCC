"""Bedrockモデル設定

このファイルでは、各エージェントが使用するBedrockモデルの設定を定義します。
モデルやパラメータを変更する場合は、このファイルを編集してください。
"""
import os
from strands.models import BedrockModel


class ModelConfig:
    """Bedrockモデル設定クラス"""

    DEFAULT_MODEL_ID = "jp.anthropic.claude-sonnet-4-5-20250929-v1:0"

    GUARDRAIL_ID = os.environ.get("GUARDRAIL_ID")
    GUARDRAIL_VERSION = os.environ.get("GUARDRAIL_VERSION", "DRAFT")

    @classmethod
    def get_model(cls) -> BedrockModel:
        """BedrockModelインスタンスを取得する

        Returns:
            BedrockModel: 設定済みのBedrockModelインスタンス
        """
        if cls.GUARDRAIL_ID:
            return BedrockModel(
                model_id=cls.DEFAULT_MODEL_ID,
                guardrail_id=cls.GUARDRAIL_ID,
                guardrail_version=cls.GUARDRAIL_VERSION,
                guardrail_trace="enabled",
            )
        return BedrockModel(model_id=cls.DEFAULT_MODEL_ID)
