"""オーケストレーターエージェント

ユーザーからの依頼を受け付け、適切な専門エージェントに振り分ける。
社内申請システムのエントリーポイントとして機能する。
"""
import logging
from datetime import date

from strands import Agent, ModelRetryStrategy, tool
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.types.exceptions import ContextWindowOverflowException, MaxTokensReachedException
from strands.types.tools import ToolContext

from config.model_config import ModelConfig
from handlers.error_handler import ErrorHandler, LoopLimitError
from handlers.loop_control_hook import LoopControlHook
from prompt.prompt_orchestrator import ORCHESTRATOR_SYSTEM_PROMPT
from session.session_manager import SessionManagerFactory

_logger = logging.getLogger(__name__)


@tool(context=True)
def set_applicant_name(name: str, tool_context: ToolContext) -> str:
    """申請者名をセッションに登録する。申請者名のバリデーション（空・500文字超チェック）完了後、
    専門エージェントへ委譲する前に必ず呼び出すこと。

    Args:
        name: 申請者名（バリデーション済みの値）
    """
    stripped = name.strip()
    if not stripped:
        return "申請者名が空です。再度お名前を入力してください。"
    if len(stripped) > 500:
        return "申請者名が長すぎます。500文字以内で入力してください。"
    tool_context.invocation_state["applicant_name"] = stripped
    _logger.info("set_applicant_name: 申請者名を登録 applicant_name=%s", stripped)
    return f"申請者名を登録しました: {stripped}"

_WELCOME_MESSAGE = """============================================================
こちらは申請受付窓口エージェントです
社内の様々な申請作業をサポートします

最初に申請者名を入力してください。その後、申請したい内容をお知らせください。キーワードでも構いません

※終了するには 'exit' または 'quit' と入力ください
※最初からやり直すには 'reset' と入力ください
============================================================"""


class OrchestratorAgent:
    """オーケストレーターエージェントクラス

    ユーザーとの対話を管理し、専門エージェントへの振り分けを行う。
    """

    def __init__(self):
        self._session_id = None
        self._session_manager = None
        self.agent = None

    def _initialize(self, transport_tool, expense_tool):
        """初期化処理"""
        self._session_id = SessionManagerFactory.generate_session_id()
        self._session_manager = SessionManagerFactory.create_session_manager(self._session_id)

        loop_control_hook = LoopControlHook(
            max_iterations=10,
            agent_name="申請受付窓口エージェント",
        )

        self.agent = Agent(
            model=ModelConfig.get_model(),
            system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
            tools=[set_applicant_name, transport_tool, expense_tool],
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
            hooks=[loop_control_hook],
            session_manager=self._session_manager,
        )

    def run(self, transport_tool, expense_tool):
        """メインインタラクションループ"""
        self._initialize(transport_tool, expense_tool)
        application_date = date.today().strftime("%Y-%m-%d")

        print(_WELCOME_MESSAGE)

        invocation_state = {
            "application_date": application_date,
            "session_id": self._session_id,
        }

        while True:
            try:
                user_input = input("\n\n入力内容（終了時はquit）: ").strip()
            except EOFError:
                break

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit"):
                print(ErrorHandler.handle_keyboard_interrupt())
                break

            if user_input.lower() in ("reset", "リセット", "最初から"):
                self._initialize(transport_tool, expense_tool)
                invocation_state = {
                    "application_date": date.today().strftime("%Y-%m-%d"),
                    "session_id": self._session_id,
                }
                print(_WELCOME_MESSAGE)
                continue

            try:
                _logger.info(
                    "reception_agent: 呼び出し開始", extra={"session_id": self._session_id}
                )
                response = self.agent(user_input, invocation_state=invocation_state)
                print(str(response))
            except KeyboardInterrupt as e:
                _logger.info(
                    "reception_agent: KeyboardInterrupt によりセッション終了",
                    extra={"session_id": self._session_id},
                )
                print(ErrorHandler.handle_keyboard_interrupt(e))
                break
            except LoopLimitError as e:
                _logger.warning(
                    "reception_agent: LoopLimitError 発生",
                    extra={"session_id": self._session_id},
                )
                print(ErrorHandler.handle_loop_limit_error(e))
            except ContextWindowOverflowException as e:
                _logger.warning(
                    "reception_agent: ContextWindowOverflowException 発生",
                    extra={"session_id": self._session_id},
                )
                print(ErrorHandler.handle_context_window_error(e))
            except MaxTokensReachedException as e:
                _logger.warning(
                    "reception_agent: MaxTokensReachedException 発生",
                    extra={"session_id": self._session_id},
                )
                print(ErrorHandler.handle_max_tokens_error(e))
            except RuntimeError as e:
                _logger.error(
                    "reception_agent: RuntimeError 発生",
                    exc_info=True,
                    extra={"session_id": self._session_id},
                )
                print(ErrorHandler.handle_runtime_error(e))
            except Exception as e:
                _logger.error(
                    "reception_agent: 予期しない例外発生",
                    exc_info=True,
                    extra={"session_id": self._session_id},
                )
                print(ErrorHandler.handle_unexpected_error(e))
