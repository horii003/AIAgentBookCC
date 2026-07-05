"""エージェント動作パラメータの一元管理

環境変数でエージェント別に上書き可能（プレフィックスはクラスごとに異なる）。
例: ECAAS_RECEPTION_MAX_ITERATIONS=15 を .env に追加するだけでチューニングできる。

使い方:
    from config.settings import settings
    loop_hook = LoopControlHook(max_iterations=settings.reception.max_iterations)
"""
from pydantic import Field
from pydantic_settings import BaseSettings


class _AgentSettings(BaseSettings):
    """全エージェント共通パラメータ（boto3/botocore リトライ設定: 最大6回, 初期遅延4秒, 最大遅延240秒）"""

    max_iterations: int = Field(10, description="ReActループ最大回数")
    max_attempts: int = Field(6, description="モデル呼び出しリトライ回数")
    initial_delay: int = Field(4, description="リトライ初期遅延（秒）")
    max_delay: int = Field(240, description="リトライ最大遅延（秒）")


class ReceptionSettings(_AgentSettings):
    """AG-001 申請受付窓口エージェント固有パラメータ

    環境変数プレフィックス: ECAAS_RECEPTION_
    例: ECAAS_RECEPTION_MAX_ITERATIONS=15
    """

    window_size: int = Field(30, description="会話ウィンドウサイズ（ターン数）")
    max_turn_count: int = Field(30, description="対話回数上限")
    max_input_length: int = Field(500, description="入力文字数上限")

    model_config = {"env_prefix": "ECAAS_RECEPTION_", "extra": "ignore"}


class TransportSettings(_AgentSettings):
    """AG-002 交通費精算申請エージェント固有パラメータ

    環境変数プレフィックス: ECAAS_TRANSPORT_
    例: ECAAS_TRANSPORT_MAX_ITERATIONS=15
    """

    window_size: int = Field(20, description="会話ウィンドウサイズ（ターン数）")
    deadline_months: int = Field(3, description="申請期限（移動日からの月数）")
    approval_threshold: int = Field(10000, description="上長承認要否閾値（円）")

    model_config = {"env_prefix": "ECAAS_TRANSPORT_", "extra": "ignore"}


class ExpenseSettings(_AgentSettings):
    """AG-003 経費精算申請エージェント固有パラメータ

    環境変数プレフィックス: ECAAS_EXPENSE_
    例: ECAAS_EXPENSE_MAX_ITERATIONS=15
    """

    window_size: int = Field(15, description="会話ウィンドウサイズ（ターン数）")
    deadline_months: int = Field(3, description="申請期限（経費発生日からの月数）")
    approval_threshold: int = Field(5000, description="上長承認要否閾値（円）")

    model_config = {"env_prefix": "ECAAS_EXPENSE_", "extra": "ignore"}


class _Settings:
    """全設定の集約クラス。`settings.{agent_name}.max_iterations` のように参照する"""

    reception: ReceptionSettings = ReceptionSettings()
    transport: TransportSettings = TransportSettings()
    expense: ExpenseSettings = ExpenseSettings()


settings = _Settings()
