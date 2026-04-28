"""交通費精算申請エージェント（AG-002）

AG-001からの委任を受けて交通費精算申請フロー全体を実行する。
"""
import logging
from datetime import date
from typing import Dict

from dateutil.relativedelta import relativedelta
from strands import Agent, tool, ToolContext
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.session.file_session_manager import FileSessionManager
from strands.types.exceptions import ContextWindowOverflowException, MaxTokensReachedException

from agent_knowledge import transportation_policies as tp
from config.model_config import ModelConfig
from handlers.error_handler import ErrorHandler
from handlers.exceptions import LoopLimitError
from hooks.human_approval_hook import HumanApprovalHook
from hooks.loop_control_hook import LoopControlHook
from tools.output_generator import generate_transport_expense_form
from tools.transport_tools import calculate_transport_expense

_logger = logging.getLogger(__name__)
_transport_agent_instances: Dict[str, Agent] = {}


def _mask_applicant_name(name: str) -> str:
    if not name:
        return ""
    return name[0] + "***"


def _is_valid_date(date_str: str) -> bool:
    try:
        date.fromisoformat(date_str)
        return True
    except (ValueError, TypeError):
        return False


def _build_transport_agent_system_prompt(
    application_date: str,
    deadline_months: int,
    manager_approval_threshold: int,
    allowed_transport_types: list,
) -> str:
    try:
        app_date = date.fromisoformat(application_date)
        deadline_date = (app_date - relativedelta(months=deadline_months)).isoformat()
    except (ValueError, TypeError):
        deadline_date = ""

    types_str = "・".join(allowed_transport_types)
    return f"""あなたは社内申請AIシステムの「交通費精算申請エージェント」です。
申請者名と申請日はすでに設定済みです（invocation_stateから取得しています）。
申請日（application_date）: {application_date}
申請期限基準日（この日付以降の移動日のみ申請可能）: {deadline_date}

【申請バリデーションルール（agent_knowledge/transportation_policies.py より）】
- 申請期限: 移動日から{deadline_months}ヶ月以内
- 上長承認が必要な閾値: 交通費合計 {manager_approval_threshold}円超
- 対応交通手段: {types_str}

【あなたの役割】
交通費精算申請フロー全体（移動情報収集・運賃計算・申請書生成・ルールチェック・最終提示）を担当します。

【処理フロー】
1. 移動情報を一区間ずつ一括入力形式で収集する（BRL-11）
   - 1区間分の移動日・出発地・目的地・交通手段をまとめて入力するよう促す
   - 入力後に内容を確認し、次の区間収集または次ステップへ進む
   - 駅名は正規形に変換してからTOOL-001に渡す（BRL-15）
   - TOOL-001（calculate_transport_expense）を呼び出して運賃を取得する（BRL-12）
     - 経路テーブルに未登録の場合は「交通費を手動で入力してください。」とユーザーへ促し手動入力値を使用する
   - 追加区間があれば繰り返す

2. 業務目的を収集する（BRL-20）
   - 業務目的が入力されていない場合は入力を促す

3. 収集済み申請情報をテキストとして整理・提示する（ドラフト提示ステップ）
   - 申請者名・申請日・全移動区間（移動日/出発地/目的地/交通手段/金額）・業務目的・合計金額を提示する
   - ※この時点ではTOOL-002を呼び出さない（テキスト提示のみ）
   - OK/修正/キャンセルの3択を取得する（BRL-06）

4. OK承認後にTOOL-002（generate_transport_expense_form）を呼び出す（HumanApprovalHookが承認ゲートとして機能）
   - applicant_name, application_date, segments（移動区間リスト）, business_purpose を渡す
   - 成功時：生成されたファイルパスをユーザーへ提示する
   - 失敗時：エラーメッセージをユーザーへ提示する

5. 申請ルールチェックを実施する（CF-005）
   - 申請期限チェック（BRL-13）: 全移動日が申請期限基準日（{deadline_date}）以降であることを確認する
     - 超過している場合はCF-008へ遷移し「申し訳ありません。経費発生日から3ヶ月を超えているため、この申請は受け付けられません。総務部門にご相談ください。」と通知する
   - 上長承認要否判定（BRL-14）: 交通費合計が{manager_approval_threshold}円を超える場合はCF-009へ遷移し上長承認確認を促す
   - 差し戻しリスク評価（BRL-08）: リスクが高い場合は警告を提示する（判定基準は要件上未定義）

6. 申請書ドラフト・チェック結果・最終提示（CF-007）
   - 申請書ドラフトのファイルパスを提示する
   - 提出操作はユーザーが実施すること（BRL-09。申請書の自動提出禁止）

【修正選択時】
- CF-003 Step 2（移動日入力）へ戻り、収集情報を最初からやり直す

【キャンセル選択時】
- 申請を中断し、セッションを終了する

【駅名正規化のルール（BRL-15）】
- TOOL-001に渡す前に、ユーザーが入力した駅名・地名を正規形（例：「渋谷」「新宿」「東京」等）に変換する
- 略称・通称（例：「渋谷駅」→「渋谷」）も正規形に変換する

【禁止事項】
- 申請書の自動提出（BRL-09）
- ドラフト提示ステップ（テキスト整理・提示）でのTOOL-002の呼び出し
- AG-001・AG-003への委任（循環呼び出し禁止）
- TOOL-001を使わずに運賃を推測・計算すること

【エラー時の振る舞い】
- TOOL-002のテンプレートファイルが見つからない・ファイル書き込みエラー等のシステム系エラーが発生した場合は、エラー内容を要約して呼び出し元エージェント（AG-001）に返すこと
- ループ上限（30回）に達した場合は「処理が複雑すぎるため終了します。最初からやり直すには「reset」と入力してください。」とユーザーへ提示する
"""


class TransportAgentFactory:
    """AG-002エージェントインスタンスをsession_idキーで管理するファクトリクラス"""

    _instances: Dict[str, Agent] = {}
    _logger = logging.getLogger(__name__)

    @classmethod
    def get_agent(cls, session_id: str, application_date: str) -> Agent:
        if session_id not in cls._instances:
            session_manager = FileSessionManager(
                session_id=session_id,
                storage_dir="data/sessions",
            )
            cls._instances[session_id] = Agent(
                model=ModelConfig.get_model(),
                system_prompt=_build_transport_agent_system_prompt(
                    application_date,
                    tp.DEADLINE_MONTHS,
                    tp.MANAGER_APPROVAL_THRESHOLD,
                    tp.ALLOWED_TRANSPORT_TYPES,
                ),
                tools=[calculate_transport_expense, generate_transport_expense_form],
                conversation_manager=SlidingWindowConversationManager(
                    window_size=20,
                    should_truncate_results=True,
                ),
                hooks=[
                    HumanApprovalHook(
                        tool_names=["generate_transport_expense_form"],
                    ),
                    LoopControlHook(max_iterations=30, agent_name="transport_agent"),
                ],
                session_manager=session_manager,
                callback_handler=None,
            )
            cls._logger.info("[AG-002] エージェントインスタンス生成: session_id=%s", session_id)
        return cls._instances[session_id]

    @classmethod
    def remove(cls, session_id: str) -> None:
        cls._instances.pop(session_id, None)


@tool(context=True)
def transport_application_agent_tool(query: str, tool_context: ToolContext) -> str:
    """交通費精算申請フロー全体（移動情報収集・運賃計算・申請書生成・ルールチェック・最終提示）を実行する。

    AG-001が交通費精算申請と判定した後に呼び出す。
    invocation_stateにsession_id・applicant_name・application_dateが設定されていること。
    """
    error_handler = ErrorHandler()
    state = tool_context.invocation_state
    session_id = state.get("session_id", "")
    applicant_name = state.get("applicant_name", "")
    application_date = state.get("application_date", "")

    _logger.info(
        "[AG-002] 交通費精算申請エージェント呼び出し: session_id=%s, applicant_name=%s, "
        "application_date=%s, query=%.50s",
        session_id,
        _mask_applicant_name(applicant_name),
        application_date,
        query,
    )

    if not applicant_name:
        return "エラー: 申請者名が設定されていません。"
    if not _is_valid_date(application_date):
        return "エラー: 申請日の形式が不正です。"

    agent = TransportAgentFactory.get_agent(session_id, application_date)
    agent_state = {
        "applicant_name": applicant_name,
        "application_date": application_date,
        "session_id": session_id,
    }

    try:
        response = agent(query, invocation_state=agent_state)
        return str(response)
    except LoopLimitError as e:
        _logger.warning(
            "[AG-002] ループ上限到達: %s/%s, session_id=%s, query=%.50s",
            e.current_iteration, e.max_iterations, session_id, query,
        )
        return error_handler.handle_loop_limit_error(e)
    except ContextWindowOverflowException as e:
        _logger.warning(
            "[AG-002] コンテキストウィンドウ超過: session_id=%s, query=%.50s", session_id, query,
        )
        return error_handler.handle_context_window_error(e)
    except MaxTokensReachedException as e:
        _logger.warning(
            "[AG-002] 最大トークン数到達: session_id=%s, query=%.50s", session_id, query,
        )
        return error_handler.handle_max_tokens_error(e)
    except RuntimeError as e:
        _logger.error(
            "[AG-002] RuntimeError: %s, session_id=%s, query=%.50s",
            str(e), session_id, query, exc_info=True,
        )
        return error_handler.handle_runtime_error(e)
    except Exception as e:
        _logger.error(
            "[AG-002] 予期しないエラー: %s, session_id=%s, query=%.50s",
            str(e), session_id, query, exc_info=True,
        )
        return error_handler.handle_unexpected_error(e)
