"""評価テスト共通ヘルパー

テレメトリ管理・エージェント生成・HumanApprovalHookパッチ・
InvocationState構築・ActorSimulator実行のユーティリティを提供する。
"""
import logging
import sys
import os
import uuid
from datetime import date
from typing import Optional
from unittest.mock import patch

from strands.models import BedrockModel
from strands_evals.telemetry import StrandsEvalsTelemetry

logger = logging.getLogger(__name__)

# ---- テレメトリ初期化（モジュールロード時に一度だけ実施） ----
_telemetry = StrandsEvalsTelemetry()
_telemetry.setup()
memory_exporter = _telemetry.get_memory_exporter()

_JUDGE_MODEL_ID = os.getenv("JUDGE_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
_DEFAULT_APPLICANT_NAME = "評価テスト太郎"
_DEFAULT_APPLICATION_DATE = date.today().strftime("%Y-%m-%d")


def get_model() -> BedrockModel:
    """LLM-as-Judge 用モデルを返す（評価対象モデルとは別モデル）"""
    return BedrockModel(model_id=_JUDGE_MODEL_ID)


def _auto_approve_callback(tool_name: str, tool_params: dict) -> tuple:
    """評価時の自動承認コールバック（常に承認）"""
    return (True, "")


def patch_human_approval_hook() -> None:
    """HumanApprovalHook の承認コールバックを自動承認に差し替える。

    load_dotenv() の直後・エージェント生成より前に呼ぶこと。
    """
    import handlers.human_approval_hook as hook_module
    original_init = hook_module.HumanApprovalHook.__init__

    def patched_init(self, approval_callback=None, approval_required_tools=None):
        original_init(
            self,
            approval_callback=_auto_approve_callback,
            approval_required_tools=approval_required_tools,
        )

    hook_module.HumanApprovalHook.__init__ = patched_init
    logger.info("HumanApprovalHook を自動承認パッチに差し替えました")


def create_orchestrator_agent(session_id: str):
    """AG-001（申請受付窓口エージェント）を本番同一構成で生成する。

    Args:
        session_id: 評価用セッション識別子（sess_ プレフィックス形式）

    Returns:
        Agent: OrchestratorAgent と同一構成のエージェントインスタンス
    """
    # sys.path にプロジェクトルートが含まれていない場合に備えて追加
    _src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _src_dir not in sys.path:
        sys.path.insert(0, _src_dir)

    from strands import Agent, ModelRetryStrategy
    from strands.agent.conversation_manager import SlidingWindowConversationManager
    from config.model_config import ModelConfig
    from handlers.loop_control_hook import LoopControlHook
    from handlers.human_approval_hook import HumanApprovalHook
    from prompt.prompt_orchestrator import ORCHESTRATOR_SYSTEM_PROMPT
    from session.session_manager import SessionManagerFactory
    from agents.transport_application_agent import transport_application_agent
    from agents.expense_application_agent import expense_application_agent

    session_manager = SessionManagerFactory.create_session_manager(session_id)

    approval_hook = HumanApprovalHook(approval_callback=_auto_approve_callback)
    loop_hook = LoopControlHook(max_iterations=10, agent_name="申請受付窓口エージェント（評価）")

    agent = Agent(
        model=ModelConfig.get_model(),
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        tools=[transport_application_agent, expense_application_agent],
        conversation_manager=SlidingWindowConversationManager(
            window_size=30,
            should_truncate_results=True,
            per_turn=False,
        ),
        callback_handler=None,
        retry_strategy=ModelRetryStrategy(
            max_attempts=6,
            initial_delay=4,
            max_delay=240,
        ),
        hooks=[approval_hook, loop_hook],
        session_manager=session_manager,
    )
    return agent


class _InvocationState:
    """invocation_state のラッパー（model_dump() で dict として返す）"""

    def __init__(self, session_id: str, application_date: str):
        self._data = {
            "session_id": session_id,
            "application_date": application_date,
        }

    def model_dump(self) -> dict:
        return dict(self._data)


def create_invocation_state(session_id: str, application_date: Optional[str] = None) -> "_InvocationState":
    """invocation_state オブジェクトを生成する。

    Args:
        session_id: セッション識別子
        application_date: 申請日（省略時は今日の日付）

    Returns:
        _InvocationState: model_dump() で dict に変換できるオブジェクト
    """
    date_str = application_date or _DEFAULT_APPLICATION_DATE
    return _InvocationState(session_id=session_id, application_date=date_str)


def generate_session_id(prefix: str = "sess") -> str:
    """評価用セッションIDを生成する（sess_UUID形式）"""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def run_actor_conversation(agent, case, invocation_state: dict) -> list:
    """ActorSimulator を使ってマルチターン会話を実行する。

    Args:
        agent: 評価対象エージェントインスタンス
        case: strands_evals.Case オブジェクト
        invocation_state: エージェントに渡す invocation_state dict

    Returns:
        list: 会話履歴（各ターンの dict リスト）
              各要素: {"user_input": str, "agent_response": str}
    """
    from strands_evals import ActorSimulator

    goal = case.metadata.get("goal", case.metadata.get("task_description", ""))
    simulator = ActorSimulator(
        goal=goal,
        initial_input=case.input,
        max_turns=30,
        model=get_model(),
    )

    turns = []
    try:
        for turn in simulator.run(agent, invocation_state=invocation_state):
            turns.append(turn)
            logger.info(
                "ターン%d: user='%s' agent='%s'",
                len(turns),
                str(turn.get("user_input", ""))[:80],
                str(turn.get("agent_response", ""))[:80],
            )
    except Exception as e:
        logger.error("ActorSimulator 例外: %s", str(e), exc_info=True)

    return turns
