# 参照: DD-02a 申請受付窓口エージェント詳細設計書
"""申請受付窓口エージェント（AG-001）定義

社員の申請意図テキスト（D-001）を受け取り、社内申請ルールナレッジ（D-002）を根拠に
交通費精算申請・経費精算申請のいずれかを判断して案内する。
申請種別が確定したら申請者名・申請日・セッションIDをinvocation_stateに設定し、
適切な専門エージェント（AG-002またはAG-003）へフロー全体を委譲する。
"""
import uuid
import logging
from datetime import datetime

from handlers.error_handler import ErrorHandler, LoopControlHook, LoopLimitError
from session.session_manager import SessionManager

logger = logging.getLogger(__name__)

try:
    from strands import Agent
    from strands.agent.conversation_manager import SlidingWindowConversationManager
    from strands.types.exceptions import ContextWindowOverflowException, MaxTokensReachedException
    _STRANDS_AVAILABLE = True
except ImportError:
    _STRANDS_AVAILABLE = False

    class ContextWindowOverflowException(Exception):
        pass

    class MaxTokensReachedException(Exception):
        pass


class OrchestratorAgent:
    """申請受付窓口エージェント（AG-001）クラス。

    責務: 社員の申請意図を受け取り、申請種別を判断して専門エージェントへ委譲する。
    制約:
      - 申請情報の収集は行わない（専門エージェントの責務）
      - 申請書の生成・提出は行わない
      - 最大対話回数: 30回（GRD-013）
    """

    def __init__(self, applicant_name: str):
        """
        Args:
            applicant_name: 申請者名（アプリケーション起動時にCLIから取得する）
        """
        self._applicant_name = applicant_name
        self._error_handler = ErrorHandler()

        # DD-02a 4.1節: セッションIDの生成（{タイムスタンプ（秒単位）}_{UUID（8文字）}形式）
        self._session_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"

        # セッションマネージャーの初期化
        self._session_manager = SessionManager(
            session_id=self._session_id,
            storage_path="data/sessions/",
        )

        logger.info(
            "OrchestratorAgent initialized: session_id=%s, applicant_name=%s",
            self._session_id, self._applicant_name,
        )

        if _STRANDS_AVAILABLE:
            from config.model_config import ModelConfig
            from prompt.prompt_orchestrator import ORCHESTRATOR_SYSTEM_PROMPT
            from agents.transport_agent import transport_agent_tool
            from agents.expense_agent import expense_agent_tool

            self.agent = Agent(
                model=ModelConfig.get_model(),
                system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
                tools=[transport_agent_tool, expense_agent_tool],
                agent_id="orchestrator_agent",
                name="申請受付窓口エージェント",
                description="申請意図から申請種別を判断して専門エージェントへ委譲する受付窓口エージェント",
                conversation_manager=SlidingWindowConversationManager(
                    window_size=30,
                    should_truncate_results=True,
                    per_turn=False,
                ),
                hooks=[LoopControlHook(max_iterations=10, agent_name="orchestrator_agent")],
                session_manager=self._session_manager.file_session_manager,
                callback_handler=None,
            )
        else:
            self.agent = None

    def _validate_input(self, user_input: str) -> str | None:
        """入力バリデーション（空文字・500文字超チェック）。

        Args:
            user_input: ユーザーからの入力テキスト

        Returns:
            str: エラーメッセージ（バリデーション失敗時）
            None: バリデーション通過時
        """
        if not user_input or not user_input.strip():
            # GRD-001: 空文字チェック
            logger.warning("Input validation failed: empty input")
            return "申請内容が入力されていません。どのような精算をされたいか、自由な言葉で入力してください。"

        # GRD-012: 500文字超チェック
        if len(user_input) > 500:
            logger.warning("Input validation failed: input too long (%d chars)", len(user_input))
            return "入力が500文字を超えています。500文字以内で再入力してください。"

        return None

    def _get_invocation_state(self) -> dict:
        """invocation_stateの辞書を組み立てて返す。

        Returns:
            dict: {applicant_name, application_date, session_id}
        """
        return {
            "applicant_name": self._applicant_name,
            "application_date": datetime.now().strftime("%Y-%m-%d"),
            "session_id": self._session_id,
        }

    def run(self) -> None:
        """対話ループを開始する。

        ウェルカムメッセージを表示した後、ユーザー入力を受け取り、
        バリデーション後にエージェントへ渡す。
        特殊コマンド（exit/quit/終了/reset/リセット/最初から）を処理する。
        """
        # DD-02a 2.2.2節: ウェルカムメッセージ
        print("=" * 60)
        print("こちらは申請受付窓口エージェントです")
        print("社内の様々な申請作業をサポートします")
        print()
        print("最初に申請者名を入力してください。その後、申請したい内容をお知らせください。キーワードでも構いません")
        print()
        print("※終了するには 'exit' または 'quit' と入力ください")
        print("※最初からやり直すには 'reset' と入力ください")
        print("=" * 60)

        # GRD-013: 対話回数カウンタ
        turn_count = 0
        # GRD-013: 最大対話回数
        MAX_TURNS = 30

        while True:
            try:
                # DD-02a 2.2.2節: 入力プロンプト
                user_input = input("\n\n入力内容（終了時はquit）: ")

                # 特殊コマンドの処理
                if user_input.strip() in ["exit", "quit", "終了"]:
                    print("ご利用ありがとうございました。")
                    break

                if user_input.strip() in ["reset", "リセット", "最初から"]:
                    # 会話履歴リセット
                    if self.agent and hasattr(self.agent, "messages"):
                        self.agent.messages = []
                    turn_count = 0
                    print("最初からやり直します。申請したい内容を入力してください。")
                    continue

                # 入力バリデーション
                error_msg = self._validate_input(user_input)
                if error_msg:
                    print(error_msg)
                    continue

                # GRD-013: 対話回数チェック
                turn_count += 1
                if turn_count > MAX_TURNS:
                    print("対話回数の上限（30回）に達しました。担当部署へご連絡ください。")
                    break

                logger.info("User input received: length=%d", len(user_input))

                # エージェントへの入力
                if not _STRANDS_AVAILABLE or self.agent is None:
                    print("（strands-agentsが未インストールのため、エージェント機能は利用できません）")
                    continue

                invocation_state = self._get_invocation_state()
                response = self.agent(user_input, invocation_state=invocation_state)
                print(str(response))

                logger.info("Delegation completed: session_id=%s", self._session_id)

            except KeyboardInterrupt as e:
                logger.info("KeyboardInterrupt: session_id=%s", self._session_id)
                print(self._error_handler.handle_keyboard_interrupt(e))
                break
            except LoopLimitError as e:
                logger.warning(
                    "LoopLimitError: %d/%d, agent=%s, session_id=%s",
                    e.current_iteration, e.max_iterations, e.agent_name, self._session_id,
                )
                print(self._error_handler.handle_loop_limit_error(e))
                continue
            except ContextWindowOverflowException as e:
                logger.warning(
                    "ContextWindowOverflowException: session_id=%s", self._session_id
                )
                print(self._error_handler.handle_context_window_error(e))
                continue
            except MaxTokensReachedException as e:
                logger.warning(
                    "MaxTokensReachedException: session_id=%s", self._session_id
                )
                print(self._error_handler.handle_max_tokens_error(e))
                continue
            except RuntimeError as e:
                logger.error(
                    "RuntimeError: %s, session_id=%s", e, self._session_id, exc_info=True
                )
                print(self._error_handler.handle_runtime_error(e))
                continue
            except Exception as e:
                logger.error(
                    "Unexpected error: %s, session_id=%s", e, self._session_id, exc_info=True
                )
                print(self._error_handler.handle_unexpected_error(e))
                continue
