"""交通費精算申請エージェント（AG-002）"""
import logging

from strands import Agent, tool
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.session.file_session_manager import FileSessionManager
from strands.types.exceptions import ContextWindowOverflowException, MaxTokensReachedException
from strands.types.tools import ToolContext

from config.model_config import ModelConfig
from handlers.error_handler import ErrorHandler
from handlers.exceptions import LoopLimitError
from handlers.hooks import HumanApprovalHook, LoopControlHook
from prompt.prompt_travel import build_travel_system_prompt
from tools.output_generator import generate_travel_expense_form
from tools.travel_tools import calculate_travel_expense

logger = logging.getLogger(__name__)

_error_handler = ErrorHandler()
_agent_instances: dict[str, Agent] = {}


def _get_travel_agent(
    session_id: str,
    applicant_name: str,
    application_date: str,
) -> Agent:
    """AG-002インスタンスを取得する（セッション内キャッシュ）。"""
    if session_id in _agent_instances:
        return _agent_instances[session_id]

    session_manager = FileSessionManager(
        session_id=session_id,
        storage_path="data/sessions/",
    )

    agent = Agent(
        system_prompt=build_travel_system_prompt(application_date),
        tools=[calculate_travel_expense, generate_travel_expense_form],
        model=ModelConfig.get_model(),
        conversation_manager=SlidingWindowConversationManager(
            window_size=20,
            should_truncate_results=True,
            per_turn=False,
        ),
        hooks=[HumanApprovalHook(), LoopControlHook(max_iterations=10)],
        callback_handler=None,
        session_manager=session_manager,
    )
    _agent_instances[session_id] = agent
    return agent


@tool(context=True)
def travel_application_agent_tool(query: str, tool_context: ToolContext) -> str:
    """交通費精算申請フロー全体を担当する専門エージェントを呼び出す。

    AG-001から委任を受け、交通費精算申請の情報収集・運賃計算・申請書生成・
    ルールチェック・最終提示を実行する。

    Args:
        query (str): 申請内容または利用者からの入力

    Returns:
        str: エージェントの応答テキスト
    """
    invocation_state = tool_context.invocation_state or {}
    session_id = invocation_state.get("session_id", "unknown")
    applicant_name = invocation_state.get("applicant_name", "")
    application_date = invocation_state.get("application_date", "")

    try:
        agent = _get_travel_agent(session_id, applicant_name, application_date)
        result = agent(
            query,
            invocation_state={
                "session_id": session_id,
                "applicant_name": applicant_name,
                "application_date": application_date,
            },
        )
        return str(result)
    except LoopLimitError as e:
        logger.warning(
            "LoopLimitError in travel_agent: %s, session_id=%s", e, session_id
        )
        return _error_handler.handle_loop_limit_error(e)
    except ContextWindowOverflowException as e:
        logger.warning(
            "ContextWindowOverflowException in travel_agent: %s, session_id=%s",
            e,
            session_id,
        )
        return _error_handler.handle_context_window_error(e)
    except MaxTokensReachedException as e:
        logger.warning(
            "MaxTokensReachedException in travel_agent: %s, session_id=%s",
            e,
            session_id,
        )
        return _error_handler.handle_max_tokens_error(e)
    except RuntimeError as e:
        logger.error(
            "RuntimeError in travel_agent: %s, session_id=%s",
            e,
            session_id,
            exc_info=True,
        )
        return _error_handler.handle_runtime_error(e)
    except Exception as e:
        logger.error(
            "Unexpected error in travel_agent: query=%s, session_id=%s",
            query[:50],
            session_id,
            exc_info=True,
        )
        return _error_handler.handle_unexpected_error(e)
