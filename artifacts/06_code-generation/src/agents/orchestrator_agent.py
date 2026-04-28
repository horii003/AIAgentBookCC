"""申請受付窓口エージェント（AG-001）"""
import logging
import os
from datetime import date

from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.session.file_session_manager import FileSessionManager
from strands.types.exceptions import ContextWindowOverflowException, MaxTokensReachedException

from handlers.error_handler import ErrorHandler
from handlers.exceptions import LoopLimitError
from handlers.hooks import LoopControlHook
from models.data_models import UserInputText
from prompt.prompt_orchestrator import ORCHESTRATOR_SYSTEM_PROMPT
from session.session_manager import SessionManagerFactory

logger = logging.getLogger(__name__)

_error_handler = ErrorHandler()


def create_orchestrator_agent(
    session_id: str,
    applicant_name: str,
    application_date: str,
) -> Agent:
    """AG-001（申請受付窓口エージェント）のインスタンスを生成して返す。

    Args:
        session_id: セッションID
        applicant_name: 申請者名
        application_date: 申請日（YYYY-MM-DD形式）

    Returns:
        Agent: 設定済みエージェントインスタンス
    """
    from agents.expense_agent import expense_application_agent_tool
    from agents.travel_agent import travel_application_agent_tool

    session_manager = FileSessionManager(
        session_id=session_id,
        storage_path="data/sessions/",
    )

    agent = Agent(
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        tools=[travel_application_agent_tool, expense_application_agent_tool],
        conversation_manager=SlidingWindowConversationManager(
            window_size=30,
            should_truncate_results=True,
            per_turn=False,
        ),
        hooks=[LoopControlHook(max_iterations=10)],
        session_manager=session_manager,
    )
    return agent


def main() -> None:
    """申請受付窓口エージェントのメインループ"""
    print("=== 社内申請システム ===")
    print("申請フローを開始します。")

    while True:
        applicant_name = input("\n申請者名を入力してください: ").strip()
        if applicant_name:
            break
        print("申請者名を入力してください。")

    application_date = date.today().isoformat()
    session_id = SessionManagerFactory.generate_session_id()
    os.makedirs(f"data/output/{session_id}", exist_ok=True)

    logger.info(
        "Application started: session_id=%s, applicant_name=%s, application_date=%s",
        session_id,
        applicant_name,
        application_date,
    )

    agent = create_orchestrator_agent(session_id, applicant_name, application_date)

    print(f"\nこんにちは、{applicant_name}さん。申請内容をお知らせください。")

    while True:
        try:
            user_input = input("\n\n入力内容（終了時はquit）: ").strip()
        except EOFError:
            break

        if user_input.lower() in ("exit", "quit"):
            print("申請システムを終了します。")
            break

        if user_input.lower() in ("reset", "リセット", "最初から"):
            logger.info("Session reset: session_id=%s", session_id)
            while True:
                applicant_name = input("\n申請者名を入力してください: ").strip()
                if applicant_name:
                    break
                print("申請者名を入力してください。")
            application_date = date.today().isoformat()
            session_id = SessionManagerFactory.generate_session_id()
            os.makedirs(f"data/output/{session_id}", exist_ok=True)
            agent = create_orchestrator_agent(session_id, applicant_name, application_date)
            print(f"\nリセットしました。{applicant_name}さん、申請内容をお知らせください。")
            continue

        try:
            from pydantic import ValidationError as PydanticValidationError
            UserInputText(text=user_input)
        except Exception as e:
            logger.warning(
                "UserInputText validation failed: input_length=%d, session_id=%s",
                len(user_input),
                session_id,
            )
            print(_error_handler.handle_validation_error(e))
            continue

        try:
            agent(
                user_input,
                invocation_state={
                    "session_id": session_id,
                    "applicant_name": applicant_name,
                    "application_date": application_date,
                },
            )
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received: session_id=%s", session_id)
            print(_error_handler.handle_keyboard_interrupt())
            break
        except LoopLimitError as e:
            logger.warning(
                "LoopLimitError in orchestrator: %s, session_id=%s", e, session_id
            )
            print(_error_handler.handle_loop_limit_error(e))
            continue
        except ContextWindowOverflowException as e:
            logger.warning(
                "ContextWindowOverflowException in orchestrator: %s, session_id=%s",
                e,
                session_id,
            )
            print(_error_handler.handle_context_window_error(e))
            continue
        except MaxTokensReachedException as e:
            logger.warning(
                "MaxTokensReachedException in orchestrator: %s, session_id=%s",
                e,
                session_id,
            )
            print(_error_handler.handle_max_tokens_error(e))
            continue
        except RuntimeError as e:
            logger.error(
                "RuntimeError in orchestrator: %s, session_id=%s",
                e,
                session_id,
                exc_info=True,
            )
            print(_error_handler.handle_runtime_error(e))
            continue
        except Exception as e:
            logger.error(
                "Unexpected error in orchestrator: %s, session_id=%s",
                e,
                session_id,
                exc_info=True,
            )
            print(_error_handler.handle_unexpected_error(e))
            continue
