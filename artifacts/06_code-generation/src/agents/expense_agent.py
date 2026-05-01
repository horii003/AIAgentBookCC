"""経費精算申請エージェント（AG-003）

AG-001 からツールとして呼び出される経費精算申請書作成専門エージェント。
経費情報の収集・OCR 自動抽出・経費区分判断・承認・申請書生成を担当する。
"""
import logging
from datetime import date, timedelta

from strands import Agent, tool, ModelRetryStrategy
from strands.types.tools import ToolContext
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands_tools import image_reader

from tools.application_generator import generate_expense_application
from session.session_manager import SessionManagerFactory
from handlers.human_approval_hook import HumanApprovalHook
from handlers.error_handler import ErrorHandler
from handlers.loop_control_hook import LoopControlHook, LoopLimitError
from prompt.prompt_expense import build_expense_prompt
from config.model_config import ModelConfig
from models.data_models import InvocationState

logger = logging.getLogger("agents.expense_agent")

MAX_LOOP_ITERATIONS = 30
WINDOW_SIZE = 15
SESSION_STORAGE_PATH = "data/sessions"

_agent_instances: dict[str, Agent] = {}


def _approval_callback(tool_name: str, tool_params: dict) -> tuple:
    """APR-001 承認コールバック: CLI で承認・修正・キャンセルを受け付ける。

    Args:
        tool_name: ツール名
        tool_params: ツールパラメータ

    Returns:
        tuple: (bool, str) - (True, "") = 承認, (False, "CANCEL") = キャンセル, (False, detail) = 修正
    """
    print(f"\n--- APR-001: 申請書生成確認 ({tool_name}) ---")
    print("申請書を生成してよろしいですか？")
    print("  OK / ok / はい / yes → 承認")
    print("  修正 / modify → 内容を修正する")
    print("  キャンセル / cancel → 取り消す")

    for _ in range(3):
        try:
            user_input = input("選択してください: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            return (False, "CANCEL")

        if user_input in {"ok", "はい", "yes", "o", "y"}:
            return (True, "")
        elif user_input in {"キャンセル", "cancel", "c", "いいえ", "no", "n"}:
            return (False, "CANCEL")
        elif user_input in {"修正", "modify", "m"}:
            detail = input("修正内容を入力してください: ").strip()
            return (False, detail or "修正")
        else:
            print("認識できない入力です。OK / 修正 / キャンセル を入力してください。")

    return (False, "CANCEL")


def _build_prompt(applicant_name: str, application_date: str) -> str:
    """AG-003 のシステムプロンプトを動的生成する。

    Args:
        applicant_name: 申請者名
        application_date: 申請日（YYYY-MM-DD 形式）

    Returns:
        str: システムプロンプト全文
    """
    return build_expense_prompt(applicant_name, application_date)


@tool(context=True)
def handle_expense_application(query: str, tool_context: ToolContext) -> str:
    """経費精算申請書作成エージェント。

    AG-001から委譲された経費精算申請フロー全体（経費情報収集・OCR自動抽出・経費区分判断・承認・申請書生成・チェック）を実行する。

    Args:
        query: AG-001 からの委譲指示文字列
        tool_context: invocation_state を含む ToolContext

    Returns:
        str: 申請書生成完了通知・申請内容チェック結果を含む文字列
    """
    state = tool_context.invocation_state or {}
    session_id = state.get("session_id", "")
    applicant_name = state.get("applicant_name", "")
    application_date = state.get("application_date", "")

    logger.info(
        f"経費精算申請エージェント呼び出し開始: session_id={session_id}, "
        f"クエリ先頭={query[:50]}"
    )

    try:
        InvocationState(
            session_id=session_id,
            applicant_name=applicant_name,
            application_date=application_date,
        )
    except Exception as e:
        logger.error(
            f"経費精算申請エージェント: バリデーションエラー: session_id={session_id}",
            exc_info=True,
        )
        return ErrorHandler.handle_validation_error(e)

    if session_id not in _agent_instances:
        logger.info(f"経費精算申請エージェント: インスタンス生成: session_id={session_id}")
        session_manager = SessionManagerFactory.create(
            session_id=session_id,
            storage_path=SESSION_STORAGE_PATH,
        )
        _agent_instances[session_id] = Agent(
            model=ModelConfig.get_model(),
            system_prompt=_build_prompt(applicant_name, application_date),
            tools=[generate_expense_application, image_reader],
            conversation_manager=SlidingWindowConversationManager(
                window_size=WINDOW_SIZE,
                should_truncate_results=True,
                per_turn=False,
            ),
            callback_handler=None,
            retry_strategy=ModelRetryStrategy(
                max_attempts=6, initial_delay=4, max_delay=240
            ),
            hooks=[
                LoopControlHook(
                    max_iterations=MAX_LOOP_ITERATIONS,
                    agent_name="expense_agent",
                ),
                HumanApprovalHook(approval_callback=_approval_callback),
            ],
            session_manager=session_manager,
        )
    else:
        logger.info(f"経費精算申請エージェント: インスタンス再利用: session_id={session_id}")

    try:
        response = _agent_instances[session_id](query, invocation_state=state)
        return str(response)
    except LoopLimitError as e:
        logger.warning(
            f"経費精算申請エージェント: ループ上限到達: session_id={session_id}, "
            f"クエリ先頭={query[:50]}"
        )
        return ErrorHandler.handle_loop_limit_error(e)
    except Exception as e:
        if "ContextWindowOverflow" in type(e).__name__:
            logger.warning(
                f"経費精算申請エージェント: コンテキストウィンドウ超過: session_id={session_id}"
            )
            return ErrorHandler.handle_context_window_error(e)
        elif "MaxTokensReached" in type(e).__name__:
            logger.warning(
                f"経費精算申請エージェント: トークン上限超過: session_id={session_id}"
            )
            return ErrorHandler.handle_max_tokens_error(e)
        elif isinstance(e, RuntimeError):
            logger.error(
                f"経費精算申請エージェント: ランタイムエラー: session_id={session_id}, "
                f"クエリ先頭={query[:50]}",
                exc_info=True,
            )
            return ErrorHandler.handle_runtime_error(e)
        else:
            logger.error(
                f"経費精算申請エージェント: 想定外エラー: session_id={session_id}, "
                f"クエリ先頭={query[:50]}",
                exc_info=True,
            )
            return ErrorHandler.handle_unexpected_error(e)
