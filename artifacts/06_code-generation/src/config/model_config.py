"""Bedrockモデル設定

各エージェントが使用するBedrockモデルの設定を一元管理する。
"""
from strands.models import BedrockModel
from strands.models.bedrock import BedrockModel as BedrockModelAlias


DEFAULT_MODEL_ID = "jp.anthropic.claude-sonnet-4-5-20250929-v1:0"


class ModelConfig:
    """Bedrockモデル設定クラス"""

    DEFAULT_MODEL_ID = DEFAULT_MODEL_ID

    @classmethod
    def get_model(cls) -> BedrockModel:
        """設定済みの BedrockModel インスタンスを返す。

        Returns:
            BedrockModel: リトライ戦略設定済みのBedrockModelインスタンス
        """
        from strands.models.bedrock import BedrockModel as BM
        return BM(
            model_id=cls.DEFAULT_MODEL_ID,
        )
