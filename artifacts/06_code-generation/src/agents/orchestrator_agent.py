"""オーケストレーターエージェント（AG-001）

ユーザーからの申請内容を受け付け、申請種別を判定して
専門エージェント（AG-002/AG-003）に処理を委任する。
"""
import logging
import uuid
from datetime import date, datetime

from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.types.exceptions import ContextWindowOverflowException, MaxTokensReachedException

from config.model_config import ModelConfig
from handlers.error_handler import ErrorHandler
from handlers.exceptions import LoopLimitError
from hooks.loop_control_hook import LoopControlHook
from models.data_models import UserInputText
from prompt.prompt_orchestrator import ORCHESTRATOR_SYSTEM_PROMPT
from session.session_manager import SessionManagerFactory

_logger = logging.getLogger(__name__)


class OrchestratorApp:
    """申請受付窓口エージェント（AG-001）アプリケーションクラス"""

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._error_handler = ErrorHandler()
        self._applicant_name = ""
        self._session_id = ""
        self._application_date = ""
        self._agent = None

    def _mask_applicant_name(self, name: str) -> str:
        if not name:
            return ""
        return name[0] + "***"

    def _collect_applicant_name(self) -> None:
        while True:
            name = input("申請者名を入力してください：").strip()
            if name:
                self._applicant_name = name
                return
            print("申請者名は空文字にできません。再度入力してください。")

    def _initialize_session(self) -> None:
        from agents.transport_agent import transport_application_agent_tool
        from agents.expense_agent import expense_application_agent_tool

        self._application_date = date.today().isoformat()
        self._session_id = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + uuid.uuid4().hex[:8]

        session_manager = SessionManagerFactory.create(self._session_id)
        loop_control_hook = LoopControlHook(max_iterations=30, agent_name="AG-001")

        self._agent = Agent(
            model=ModelConfig.get_model(),
            system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
            tools=[transport_application_agent_tool, expense_application_agent_tool],
            conversation_manager=SlidingWindowConversationManager(
                window_size=30,
                should_truncate_results=True,
            ),
            callback_handler=None,
            hooks=[loop_control_hook],
            session_manager=session_manager,
        )

        self._logger.info(
            "[AG-001] 申請受付窓口エージェント起動: session_id=%s, applicant_name=%s, application_date=%s",
            self._session_id,
            self._mask_applicant_name(self._applicant_name),
            self._application_date,
        )

    def _reset_session(self) -> None:
        from agents.transport_agent import _transport_agent_instances
        from agents.expense_agent import _expense_agent_instances

        self._logger.warning(
            "[AG-001] リセットコマンド受信: セッション再初期化: session_id=%s",
            self._session_id,
        )
        _transport_agent_instances.pop(self._session_id, None)
        _expense_agent_instances.pop(self._session_id, None)

        self._collect_applicant_name()
        self._initialize_session()

    def run(self) -> None:
        welcome = (
            "============================================================\n"
            "こちらは申請受付窓口エージェントです\n"
            "社内の様々な申請作業をサポートします\n\n"
            "最初に申請者名を入力してください。その後、申請したい内容をお知らせください。キーワードでも構いません\n\n"
            "※終了するには 'exit' または 'quit' と入力ください\n"
            "※最初からやり直すには 'reset' と入力ください\n"
            "============================================================"
        )
        print(welcome)

        self._collect_applicant_name()
        self._initialize_session()

        while True:
            try:
                user_input = input("\n\n入力内容（終了時はquit）: ").strip()

                if user_input.lower() in ("exit", "quit", "終了"):
                    break

                if user_input.lower() in ("reset", "リセット", "最初から"):
                    self._reset_session()
                    continue

                try:
                    UserInputText(text=user_input)
                except Exception:
                    print("入力内容が不正です。1〜500文字で入力してください。")
                    continue

                invocation_state = {
                    "session_id": self._session_id,
                    "applicant_name": self._applicant_name,
                    "application_date": self._application_date,
                }
                response = self._agent(user_input, invocation_state=invocation_state)
                print(str(response))

            except KeyboardInterrupt as e:
                self._logger.info("[AG-001] ユーザーによる中断: session_id=%s", self._session_id)
                print(self._error_handler.handle_keyboard_interrupt())
                break
            except LoopLimitError as e:
                self._logger.warning(
                    "[AG-001] ループ上限到達: %s/%s, session_id=%s",
                    e.current_iteration, e.max_iterations, self._session_id,
                )
                print(self._error_handler.handle_loop_limit_error(e))
                continue
            except ContextWindowOverflowException as e:
                self._logger.warning("[AG-001] コンテキストウィンドウ超過: session_id=%s", self._session_id)
                print(self._error_handler.handle_context_window_error(e))
                continue
            except MaxTokensReachedException as e:
                self._logger.warning("[AG-001] 最大トークン数到達: session_id=%s", self._session_id)
                print(self._error_handler.handle_max_tokens_error(e))
                continue
            except RuntimeError as e:
                self._logger.error(
                    "[AG-001] RuntimeError: %s, session_id=%s", str(e), self._session_id, exc_info=True,
                )
                print(self._error_handler.handle_runtime_error(e))
                continue
            except Exception as e:
                self._logger.error(
                    "[AG-001] 予期しないエラー: %s, session_id=%s", str(e), self._session_id, exc_info=True,
                )
                print(self._error_handler.handle_unexpected_error(e))
                continue


def main() -> None:
    OrchestratorApp().run()
