"""申請受付窓口エージェント（AG-001）

社員の申請意図を受け付けて申請種別を判断し、専門エージェント（AG-002/AG-003）に委譲する。
マルチエージェントシステムの入口として、セッション管理・ルーティングを担当する。
"""
import logging
import uuid
from datetime import date, datetime

from strands import Agent, ModelRetryStrategy
from strands.agent.conversation_manager import SlidingWindowConversationManager

from agents.transport_agent import handle_transport_expense_application
from agents.expense_agent import handle_expense_application
from session.session_manager import SessionManagerFactory
from handlers.error_handler import ErrorHandler
from handlers.loop_control_hook import LoopControlHook, LoopLimitError
from prompt.prompt_orchestrator import ORCHESTRATOR_SYSTEM_PROMPT
from config.model_config import ModelConfig
from models.data_models import InvocationState

logger = logging.getLogger("agents.orchestrator_agent")

MAX_LOOP_ITERATIONS = 30
MAX_INPUT_LENGTH = 500
MAX_TURNS = 30
WINDOW_SIZE = 30
SESSION_STORAGE_PATH = "data/sessions"

WELCOME_MESSAGE = """============================================================
こちらは申請受付窓口エージェントです
社内の様々な申請作業をサポートします

最初に申請者名を入力してください。その後、申請したい内容をお知らせください。キーワードでも構いません

※終了するには 'exit' または 'quit' と入力ください
※最初からやり直すには 'reset' と入力ください
============================================================"""

INPUT_PROMPT = "\n\n入力内容（終了時はquit）: "

RESET_COMMANDS = {"reset", "リセット", "最初から"}
EXIT_COMMANDS = {"exit", "quit", "終了"}


def _generate_session_id() -> str:
    """セッション ID をタイムスタンプ_UUID8 形式で生成する。"""
    return datetime.now().strftime("%Y%m%d%H%M%S") + "_" + uuid.uuid4().hex[:8]


def _create_ag001_agent(session_id: str) -> Agent:
    """AG-001 Agent インスタンスを生成するファクトリ関数。

    Args:
        session_id: セッション ID

    Returns:
        Agent: 初期化済みの AG-001 Agent インスタンス
    """
    loop_control_hook = LoopControlHook(
        max_iterations=MAX_LOOP_ITERATIONS,
        agent_name="AG-001",
    )
    return Agent(
        model=ModelConfig.get_model(),
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        tools=[handle_transport_expense_application, handle_expense_application],
        conversation_manager=SlidingWindowConversationManager(
            window_size=WINDOW_SIZE,
            should_truncate_results=True,
            per_turn=False,
        ),
        callback_handler=None,
        retry_strategy=ModelRetryStrategy(
            max_attempts=6, initial_delay=4, max_delay=240
        ),
        hooks=[loop_control_hook],
        session_manager=SessionManagerFactory.create(
            session_id=session_id,
            storage_path=SESSION_STORAGE_PATH,
        ),
    )


def _run_repl(agent: Agent, session_id: str) -> None:
    """対話ループを実行する。

    Args:
        agent: AG-001 Agent インスタンス
        session_id: セッション ID
    """
    turn_count = 0
    applicant_name = ""
    print(WELCOME_MESSAGE)

    while turn_count < MAX_TURNS:
        try:
            user_input = input(INPUT_PROMPT)
        except KeyboardInterrupt as e:
            logger.info(f"申請受付窓口エージェント: キーボード割り込み: session_id={session_id}")
            print("\n" + ErrorHandler.handle_keyboard_interrupt(e))
            break
        except EOFError:
            break

        if user_input.strip() in EXIT_COMMANDS:
            logger.info(f"申請受付窓口エージェント: セッション終了: session_id={session_id}, status=CLOSED")
            break

        if user_input.strip() in RESET_COMMANDS:
            return None

        if len(user_input) > MAX_INPUT_LENGTH:
            print("入力が500文字を超えています。500文字以内に短縮してから再入力してください。")
            continue

        if not applicant_name and turn_count == 0:
            applicant_name = user_input.strip()

        state = InvocationState(
            session_id=session_id,
            applicant_name=applicant_name,
            application_date=date.today().isoformat(),
        ).model_dump()

        try:
            response = agent(user_input, invocation_state=state)
            print(str(response))
        except KeyboardInterrupt as e:
            logger.info(f"申請受付窓口エージェント: キーボード割り込み: session_id={session_id}")
            print("\n" + ErrorHandler.handle_keyboard_interrupt(e))
            break
        except LoopLimitError as e:
            logger.warning(f"申請受付窓口エージェント: ループ上限到達: session_id={session_id}")
            print(ErrorHandler.handle_loop_limit_error(e))
        except Exception as e:
            if "ContextWindowOverflow" in type(e).__name__:
                logger.warning(f"申請受付窓口エージェント: コンテキストウィンドウ超過: session_id={session_id}")
                print(ErrorHandler.handle_context_window_error(e))
            elif "MaxTokensReached" in type(e).__name__:
                logger.warning(f"申請受付窓口エージェント: トークン上限超過: session_id={session_id}")
                print(ErrorHandler.handle_max_tokens_error(e))
            elif isinstance(e, RuntimeError):
                logger.error(f"申請受付窓口エージェント: ランタイムエラー: session_id={session_id}", exc_info=True)
                print(ErrorHandler.handle_runtime_error(e))
            else:
                logger.error(f"申請受付窓口エージェント: 想定外エラー: session_id={session_id}", exc_info=True)
                print(ErrorHandler.handle_unexpected_error(e))

        turn_count += 1

    if turn_count >= MAX_TURNS:
        logger.warning(f"申請受付窓口エージェント: 対話回数上限到達: session_id={session_id}, turns=30")
        print("対話回数の上限に達しました。管理部門（経理部）にお問い合わせいただくか、改めて最初からお試しください。")

    return True


def run() -> None:
    """CLI のエントリポイント。session_id を生成し、対話ループを実行する。"""
    while True:
        session_id = _generate_session_id()
        logger.info(f"申請受付窓口エージェント起動: session_id={session_id}")

        agent = _create_ag001_agent(session_id)
        result = _run_repl(agent, session_id)

        if result is None:
            continue
        break
