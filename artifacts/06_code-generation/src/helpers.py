"""評価スクリプト共通ヘルパーモジュール"""
from datetime import date

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from strands import Agent
from strands.models import BedrockModel

from agents.orchestrator_agent import create_orchestrator_agent
from handlers.human_approval_hook import patch_human_approval_hook  # noqa: F401 (re-exported)
from models.data_models import InvocationState
from session.session_manager import SessionManagerFactory

memory_exporter = InMemorySpanExporter()
_provider = TracerProvider()
_provider.add_span_processor(SimpleSpanProcessor(memory_exporter))


def create_reception_agent(session_id: str) -> Agent:
    """受付エージェント（AG-001）のインスタンスを生成して返す。"""
    return create_orchestrator_agent()


def get_model() -> BedrockModel:
    """評価用 LLM モデルのインスタンスを返す。"""
    return BedrockModel(model_id="jp.anthropic.claude-sonnet-4-5-20250929-v1:0")


def create_invocation_state(session_id: str) -> InvocationState:
    """エージェント呼び出しに必要な状態オブジェクトを生成して返す。"""
    return InvocationState(
        session_id=session_id,
        applicant_name="評価ユーザー",
        application_date=date.today().isoformat(),
    )


def run_actor_conversation(agent: Agent, case, invocation_state: dict) -> list[dict]:
    """ActorSimulator によるマルチターン会話を実行し、ターンリストを返す。

    Returns:
        list[dict]: [{"user_input": str, "agent_response": str}, ...]
    """
    try:
        from strands_evals.actor import ActorSimulator
    except ImportError:
        from strands_evals import ActorSimulator

    simulator = ActorSimulator(model=get_model(), goal=case.metadata.get("goal", ""))
    turns = []

    user_input = case.input
    while True:
        agent_response = str(agent(user_input, invocation_state=invocation_state))
        turns.append({"user_input": user_input, "agent_response": agent_response})

        next_input = simulator.get_next_input(agent_response)
        if next_input is None:
            break
        user_input = next_input

    return turns
