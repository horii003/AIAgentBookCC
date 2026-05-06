# 参照: DD-06 評価テスト詳細設計書, SD-08 評価テスト共通設計
"""評価テスト用ヘルパーモジュール

評価スクリプト（eval_tool_selection.py / eval_goal_success.py）から利用する
共通ヘルパー関数・オブジェクトを提供する。
"""
import logging
import sys
import os
from unittest.mock import patch, MagicMock

logger = logging.getLogger(__name__)

# HumanApprovalHookのモックフラグ
_hook_patched = False


def patch_human_approval_hook() -> None:
    """HumanApprovalHookの_approval_callbackをモックして自動的にOKを返すようにする。

    評価実行中の人間承認待ちを自動化し、評価がブロックされないようにする。
    load_dotenv()の直後、エージェント生成より前に必ず呼び出すこと。
    """
    global _hook_patched
    if _hook_patched:
        return

    try:
        from handlers.error_handler import HumanApprovalHook
        # _approval_callbackをモックして常にOKを返す
        HumanApprovalHook._approval_callback = lambda self, tool_name, tool_params: (True, "")
        _hook_patched = True
        logger.info("HumanApprovalHookのモック化が完了しました（自動OK）")
    except Exception as e:
        logger.warning("HumanApprovalHookのモック化に失敗しました: %s", e)


def create_reception_agent(session_id: str):
    """AG-001（申請受付窓口エージェント）インスタンスを生成して返す。

    Args:
        session_id: 評価用セッションID

    Returns:
        AG-001のAgentインスタンス
    """
    try:
        from config.model_config import ModelConfig
        from prompt.prompt_orchestrator import ORCHESTRATOR_SYSTEM_PROMPT
        from agents.transport_agent import transport_agent_tool
        from agents.expense_agent import expense_agent_tool
        from handlers.error_handler import LoopControlHook
        from session.session_manager import SessionManager
        from strands import Agent
        from strands.agent.conversation_manager import SlidingWindowConversationManager

        session_manager = SessionManager(
            session_id=session_id,
            storage_path="data/sessions/",
        )

        agent = Agent(
            model=ModelConfig.get_model(),
            system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
            tools=[transport_agent_tool, expense_agent_tool],
            agent_id="orchestrator_agent",
            name="申請受付窓口エージェント",
            conversation_manager=SlidingWindowConversationManager(
                window_size=30,
                should_truncate_results=True,
                per_turn=False,
            ),
            hooks=[LoopControlHook(max_iterations=10, agent_name="orchestrator_agent")],
            session_manager=session_manager.file_session_manager,
            callback_handler=None,
        )
        return agent
    except Exception as e:
        logger.error("create_reception_agentに失敗しました: %s", e, exc_info=True)
        raise


def create_invocation_state(session_id: str):
    """評価用のinvocation_state辞書を生成して返す。

    Args:
        session_id: セッションID

    Returns:
        invocation_state辞書（applicant_name/application_date/session_id）
    """
    from datetime import datetime
    return {
        "applicant_name": "評価テストユーザー",
        "application_date": datetime.now().strftime("%Y-%m-%d"),
        "session_id": session_id,
    }


def run_actor_conversation(agent, case, invocation_state: dict) -> list:
    """ActorSimulatorによるマルチターン会話を実行する。

    Args:
        agent: AG-001のAgentインスタンス
        case: strands_evals.Caseオブジェクト
        invocation_state: エージェント呼び出し時のinvocation_state辞書

    Returns:
        list: 各ターンの {"user_input": str, "agent_response": str} 辞書のリスト
    """
    try:
        from strands_evals import ActorSimulator
        actor = ActorSimulator(
            goal=case.metadata.get("goal", ""),
            model=get_model(),
        )

        turns = []
        current_input = case.input

        for _ in range(10):  # 最大10ターン
            response = agent(current_input, invocation_state=invocation_state)
            turn = {"user_input": current_input, "agent_response": str(response)}
            turns.append(turn)

            # ActorSimulatorで次のユーザー入力を生成する
            next_input = actor.generate_next_input(str(response))
            if next_input is None or actor.is_goal_achieved(str(response)):
                break
            current_input = next_input

        return turns
    except Exception as e:
        logger.warning("run_actor_conversationで例外が発生しました: %s", e)
        # フォールバック: シングルターンのみ実行
        response = agent(case.input, invocation_state=invocation_state)
        return [{"user_input": case.input, "agent_response": str(response)}]


def get_model():
    """評価用LLMモデルを返す。

    Returns:
        BedrockModelインスタンス
    """
    from config.model_config import ModelConfig
    return ModelConfig.get_model()


# OpenTelemetryスパンのインメモリ収集器
try:
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor

    memory_exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(memory_exporter))

except ImportError:
    # opentelemetry未インストール環境向けスタブ
    class _StubExporter:
        def clear(self):
            pass
        def get_finished_spans(self):
            return []

    memory_exporter = _StubExporter()
    logger.warning("opentelemetryがインストールされていません。テレメトリ収集は無効です。")
