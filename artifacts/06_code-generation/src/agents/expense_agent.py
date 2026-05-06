# 参照: DD-02c 経費精算申請エージェント詳細設計書
"""経費精算申請エージェント（AG-003）のAgent as Tools定義

AG-001（申請受付窓口エージェント）からexpense_agent_toolとして呼び出される。
session_idをキーとしてAgentインスタンスをモジュールレベル辞書でキャッシュし、
セッション内での会話履歴を保持する。
"""
import logging

from handlers.error_handler import ErrorHandler, LoopControlHook, LoopLimitError, HumanApprovalHook

logger = logging.getLogger(__name__)
_error_handler = ErrorHandler()

# DD-02c 2.5.2節: session_idをキーにしてAgentインスタンスをキャッシュする
_agent_instances: dict = {}

try:
    from strands import Agent, tool, ToolContext
    from strands.agent.conversation_manager import SlidingWindowConversationManager
    from strands.types.exceptions import ContextWindowOverflowException, MaxTokensReachedException
    _STRANDS_AVAILABLE = True
except ImportError:
    _STRANDS_AVAILABLE = False

    def tool(context=False):
        def decorator(func):
            return func
        return decorator if context else lambda func: func

    class ToolContext:
        def __init__(self):
            self.invocation_state = {}

    class ContextWindowOverflowException(Exception):
        pass

    class MaxTokensReachedException(Exception):
        pass


@tool(context=True)
def expense_agent_tool(
    query: str,
    tool_context: "ToolContext" = None,
) -> str:
    """経費精算申請フローを実行します。

    AG-001（申請受付窓口エージェント）から委譲メッセージ（申請種別：経費精算申請・申請意図テキスト）を受け取り、
    経費精算申請に必要な情報収集・領収書自動読み取り・申請書作成・チェックを実行します。

    Args:
        query: 委譲メッセージ（申請種別・申請意図テキストを含む）
        tool_context: invocation_stateを含むToolContext（@tool(context=True)により自動注入）

    Returns:
        str: AG-003の処理完了応答テキスト（エラー時もstr）
    """
    # invocation_stateからsession_id・applicant_name・application_dateを取得する
    state = {}
    if tool_context and hasattr(tool_context, "invocation_state") and tool_context.invocation_state:
        state = tool_context.invocation_state

    session_id = state.get("session_id", "")
    applicant_name = state.get("applicant_name", "")
    application_date = state.get("application_date", "")

    logger.info(
        "expense_agent_tool invoked: session_id=%s, applicant_name=%s",
        session_id, applicant_name,
    )

    try:
        if not _STRANDS_AVAILABLE:
            return "strands-agentsがインストールされていないため実行できません。"

        # session_id未登録の場合のみ新しいAgentインスタンスを生成する
        if session_id not in _agent_instances:
            from config.model_config import ModelConfig
            from prompt.prompt_expense import get_expense_system_prompt
            from tools.output_generator import generate_expense_application
            from session.session_manager import SessionManager

            # image_readerはstrands_toolsから取得（利用可能な場合）
            tools_list = [generate_expense_application]
            try:
                from strands_tools import image_reader
                tools_list.insert(0, image_reader)
            except ImportError:
                logger.warning("strands_tools.image_reader が利用できません。領収書自動読み取りは無効になります。")

            session_manager = SessionManager(
                session_id=session_id,
                storage_path="data/sessions/",
            )

            _agent_instances[session_id] = Agent(
                model=ModelConfig.get_model(),
                system_prompt=get_expense_system_prompt(applicant_name, application_date),
                tools=tools_list,
                agent_id="expense_agent",
                name="経費精算申請エージェント",
                description="経費精算申請フロー全体（情報収集・領収書自動読み取り・申請書作成・チェック）を実行する専門エージェント",
                conversation_manager=SlidingWindowConversationManager(
                    window_size=15,
                    should_truncate_results=True,
                    per_turn=False,
                ),
                hooks=[
                    HumanApprovalHook(),
                    LoopControlHook(max_iterations=10, agent_name="expense_agent"),
                ],
                session_manager=session_manager.file_session_manager,
                callback_handler=None,
            )

        # invocation_stateはAG-003内部向けに渡す（session_idは除外）
        agent_state = {
            "applicant_name": applicant_name,
            "application_date": application_date,
        }
        response = _agent_instances[session_id](query, invocation_state=agent_state)
        return str(response)

    except LoopLimitError as e:
        logger.warning(
            "LoopLimitError: %d/%d, agent=%s, query=%s",
            e.current_iteration, e.max_iterations, e.agent_name, query[:50],
        )
        return _error_handler.handle_loop_limit_error(e)
    except ContextWindowOverflowException as e:
        logger.warning(
            "ContextWindowOverflowException: session_id=%s, query=%s",
            session_id, query[:50],
        )
        return _error_handler.handle_context_window_error(e)
    except MaxTokensReachedException as e:
        logger.warning(
            "MaxTokensReachedException: session_id=%s, query=%s",
            session_id, query[:50],
        )
        return _error_handler.handle_max_tokens_error(e)
    except RuntimeError as e:
        logger.error(
            "RuntimeError in expense_agent_tool: %s, query=%s",
            e, query[:50], exc_info=True,
        )
        return _error_handler.handle_runtime_error(e)
    except Exception as e:
        logger.error(
            "Unexpected error in expense_agent_tool: %s, query=%s",
            e, query[:50], exc_info=True,
        )
        return _error_handler.handle_unexpected_error(e)
