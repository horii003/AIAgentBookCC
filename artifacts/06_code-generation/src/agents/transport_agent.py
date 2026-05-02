import logging

from strands import Agent, tool
from strands.models import BedrockModel
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.types.tools import ToolContext

from handlers.error_handler import ErrorHandler
from handlers.human_approval_hook import HumanApprovalHook, approval_callback
from handlers.loop_control_hook import LoopControlHook, LoopLimitError
from prompt.prompt_transport import get_transport_agent_system_prompt
from tools.transport_tools import calculate_transport_fare
from tools.form_generator import generate_transport_expense_form

logger = logging.getLogger(__name__)
error_handler = ErrorHandler()

_agent_instances: dict[str, Agent] = {}


def _build_transport_agent(application_date: str) -> Agent:
    return Agent(
        model=BedrockModel(model_id="jp.anthropic.claude-sonnet-4-5-20250929-v1:0"),
        system_prompt=get_transport_agent_system_prompt(application_date),
        tools=[calculate_transport_fare, generate_transport_expense_form],
        conversation_manager=SlidingWindowConversationManager(window_size=20),
        hooks=[LoopControlHook(max_iterations=10), HumanApprovalHook(approval_callback=approval_callback)],
        callback_handler=None,
    )


@tool(context=True)
def transport_agent_tool(
    tool_context: ToolContext,
    application_type: str,
    applicant_name: str,
    user_input_text: str,
) -> str:
    """交通費精算申請エージェント（AG-002）を呼び出し、移動情報の収集・交通費計算・申請書生成を行う。

    AG-001が申請種別「交通費精算申請」と確定した後に呼び出す。

    Args:
        application_type: 申請種別（"交通費精算申請"確定済み）
        applicant_name: 申請者名
        user_input_text: 社員の申請内容テキスト

    Returns:
        str: AG-002エージェントからの応答テキスト
    """
    state = tool_context.invocation_state
    session_id = state.get("session_id", "")
    application_date = state.get("application_date", "")
    masked_name = (applicant_name[:1] + "***") if applicant_name else "***"

    logger.info(f"[OPE-002] transport_agent_tool 開始: session_id={session_id}, applicant_name={masked_name}")

    if session_id not in _agent_instances:
        logger.info(f"[OPE-002] AG-002 新規インスタンス生成: session_id={session_id}")
        _agent_instances[session_id] = _build_transport_agent(application_date)
    else:
        logger.info(f"[OPE-002] AG-002 キャッシュ再利用: session_id={session_id}")

    try:
        response = _agent_instances[session_id](user_input_text, invocation_state=state)
        logger.info(f"[OPE-002] transport_agent_tool 完了: session_id={session_id}")
        return str(response)
    except LoopLimitError as e:
        logger.error(f"[ERR-008] ループ上限: session_id={session_id}, agent={e.agent_name}, count={e.current_iteration}/{e.max_iterations}")
        return error_handler.handle_loop_limit_error(e)
    except RuntimeError as e:
        logger.error(f"[ERR-007] RuntimeError: session_id={session_id}, query={user_input_text[:50]}")
        return error_handler.handle_runtime_error(e)
    except Exception as e:
        logger.error(f"[ERR-008] 想定外例外: session_id={session_id}, query={user_input_text[:50]}, error={str(e)[:100]}")
        return error_handler.handle_unexpected_error(e)
