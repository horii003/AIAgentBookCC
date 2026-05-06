# 参照: SD-06 共通設定方針, SD-01 システム基本情報
"""Bedrockモデル設定

各エージェント（AG-001〜AG-003）が使用するAmazon BedrockモデルとGaurdreailの設定を一元管理する。
LLMモデルID・ガードレールID・ガードレールバージョンは環境変数で制御できるよう設計する。
"""
import os
from strands.models import BedrockModel


class ModelConfig:
    """Amazon Bedrockモデル設定クラス。

    責務: 全エージェントが使用するBedrockModelインスタンスの設定を一元管理する。
    制約:
      - DEFAULT_MODEL_ID: R10準拠。日本リージョン用モデルID
      - GUARDRAIL_ID: 要件上未定義。環境変数GUARDRAIL_IDで設定する
      - GUARDRAIL_VERSION: 環境変数GUARDRAIL_VERSIONで設定。デフォルト「DRAFT」
    """

    # R10: LLMモデルID（jp.anthropic.claude-sonnet-4-5-20250929-v1:0）
    DEFAULT_MODEL_ID: str = "jp.anthropic.claude-sonnet-4-5-20250929-v1:0"

    # ガードレールID: 要件上未定義（環境変数で設定）
    GUARDRAIL_ID: str = os.getenv("GUARDRAIL_ID", "")

    # ガードレールバージョン: デフォルトDRAFT（環境変数で上書き可能）
    GUARDRAIL_VERSION: str = os.getenv("GUARDRAIL_VERSION", "DRAFT")

    @classmethod
    def get_model(cls) -> BedrockModel:
        """BedrockModelインスタンスを取得する。

        Returns:
            BedrockModel: ガードレール・トレース設定済みのBedrockModelインスタンス

        Note:
            R10: guardrail_trace="enabled"は全エージェント共通設定
        """
        # R10: ガードレールトレース有効化（全エージェント共通）
        return BedrockModel(
            model_id=cls.DEFAULT_MODEL_ID,
            guardrail_id=cls.GUARDRAIL_ID if cls.GUARDRAIL_ID else None,
            guardrail_version=cls.GUARDRAIL_VERSION,
            guardrail_trace="enabled",
        )
