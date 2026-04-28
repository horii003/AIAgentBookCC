"""Bedrockモデル設定

各エージェントが使用するBedrockモデルの設定を一元管理する。
モデルIDやリトライ戦略をプロジェクト要件に応じて変更する場合は、このファイルを編集する。
"""
from strands import ModelRetryStrategy
from strands.models import BedrockModel


DEFAULT_MODEL_ID = "jp.anthropic.claude-sonnet-4-5-20250929-v1:0"


class ModelConfig:
    """Bedrockモデル設定クラス"""

    DEFAULT_MODEL_ID: str = DEFAULT_MODEL_ID

    @classmethod
    def get_model(cls) -> BedrockModel:
        """設定済みのBedrockModelインスタンスを返す"""
        return BedrockModel(model_id=cls.DEFAULT_MODEL_ID)

    @classmethod
    def get_retry_strategy(cls) -> ModelRetryStrategy:
        """エージェントに設定するリトライ戦略を返す（max_attempts=6, initial_delay=4, max_delay=240）"""
        return ModelRetryStrategy(
            max_attempts=6,
            initial_delay=4,
            max_delay=240,
        )
