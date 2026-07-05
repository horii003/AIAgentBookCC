"""Bedrockモデル設定

各エージェントが使用するBedrockモデルの設定を定義します。
モデルやパラメータを変更する場合は、このファイルを編集してください。
"""
from functools import lru_cache

from strands.models import BedrockModel


class ModelConfig:
    """Bedrockモデル設定クラス"""

    DEFAULT_MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

    # ガードレール設計上はApplicationレベルのカスタム実装（Amazon Bedrock Guardrails未使用）
    GUARDRAIL_ID = None
    GUARDRAIL_VERSION = "DRAFT"

    @classmethod
    @lru_cache(maxsize=1)
    def get_model(cls) -> BedrockModel:
        """設定済みのBedrockModelインスタンスを返す"""
        if cls.GUARDRAIL_ID is not None:
            return BedrockModel(
                model_id=cls.DEFAULT_MODEL_ID,
                guardrail_id=cls.GUARDRAIL_ID,
                guardrail_version=cls.GUARDRAIL_VERSION,
                guardrail_trace="enabled",
            )
        return BedrockModel(model_id=cls.DEFAULT_MODEL_ID)
