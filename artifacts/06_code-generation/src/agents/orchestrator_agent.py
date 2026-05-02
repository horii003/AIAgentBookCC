import logging
from datetime import date

from strands import Agent
from strands.models import BedrockModel
from strands.agent.conversation_manager import SlidingWindowConversationManager

from agents.transport_agent import transport_agent_tool
from agents.expense_agent import expense_agent_tool
from handlers.error_handler import ErrorHandler
from handlers.loop_control_hook import LoopControlHook, LoopLimitError
from prompt.prompt_orchestrator import get_orchestrator_system_prompt

logger = logging.getLogger(__name__)
error_handler = ErrorHandler()


def create_orchestrator_agent() -> Agent:
    """申請受付窓口エージェント（AG-001）インスタンスを生成する。"""
    return Agent(
        model=BedrockModel(model_id="jp.anthropic.claude-sonnet-4-5-20250929-v1:0"),
        system_prompt=get_orchestrator_system_prompt(),
        tools=[transport_agent_tool, expense_agent_tool],
        conversation_manager=SlidingWindowConversationManager(window_size=30),
        hooks=[LoopControlHook(max_iterations=10)],
    )
