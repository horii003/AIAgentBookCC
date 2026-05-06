# 参照: DD-03 ハンドラー詳細設計書
"""エラーハンドリング・ループ制御・人間承認フックの定義

`handlers/error_handler.py` に `LoopLimitError`・`ErrorHandler`・`HumanApprovalHook`・
`LoopControlHook` の4クラスを集約し、全エージェント（AG-001〜AG-003）と全ツールの
例外処理・人間承認制御・ループ制御を一元管理する。
"""
import logging
from typing import Any, Optional

try:
    from pydantic import ValidationError
except ImportError:
    ValidationError = None

try:
    from strands.hooks import (
        HookProvider,
        HookRegistry,
        BeforeInvocationEvent,
        AfterModelCallEvent,
        BeforeModelCallEvent,
        AfterInvocationEvent,
        BeforeToolCallEvent,
        AfterToolCallEvent,
    )
except ImportError:
    # strands未インストール環境でもテストできるようにスタブを定義
    class HookProvider:
        pass

    class HookRegistry:
        def add_callback(self, *args, **kwargs):
            pass

    class BeforeInvocationEvent:
        pass

    class AfterModelCallEvent:
        exception = None

    class BeforeModelCallEvent:
        pass

    class AfterInvocationEvent:
        pass

    class BeforeToolCallEvent:
        tool_use = {}
        cancel_tool = False

    class AfterToolCallEvent:
        tool_use = {}


logger = logging.getLogger(__name__)


# ============================================================
# LoopLimitError カスタム例外クラス
# ============================================================

class LoopLimitError(Exception):
    """ReActループ上限到達時のカスタム例外。

    責務: LoopControlHookがReActループ上限に到達したときに発生させる。
    制約: current_iteration・max_iterations・agent_nameの3フィールドを保持する。
    """

    def __init__(self, current_iteration: int, max_iterations: int, agent_name: str):
        """
        Args:
            current_iteration: 上限到達時の現在のループ回数
            max_iterations: 設定されたループ上限回数
            agent_name: LoopLimitErrorが発生したエージェント名
        """
        self.current_iteration = current_iteration
        self.max_iterations = max_iterations
        self.agent_name = agent_name
        super().__init__(
            f"Loop limit reached: {current_iteration}/{max_iterations} iterations in agent '{agent_name}'"
        )


# ============================================================
# ErrorHandler クラス
# ============================================================

class ErrorHandler:
    """例外種別に対応するユーザー向け日本語メッセージを生成して返すクラス。

    責務: 各エージェント・ツールから委譲された例外に対して、ユーザー向け日本語メッセージ
    文字列を生成して返すことのみを担当する。
    非責務: ログ出力（呼び出し元が ErrorHandler 呼び出し前に実施する）、
    セッション状態更新、ガードレール判定。
    制約: ステートレスクラス（インスタンス変数なし）。
    """

    def __init__(self):
        pass

    def handle_throttling_error(self, e) -> str:
        """APIレート制限エラー（ModelThrottledException）のメッセージを生成する。

        Args:
            e: 発生した例外

        Returns:
            str: ユーザー向け日本語エラーメッセージ
        """
        return "現在APIの利用制限に達しています。しばらくしてから再度お試しください。"

    def handle_max_tokens_error(self, e) -> str:
        """最大トークン数到達エラー（MaxTokensReachedException）のメッセージを生成する。

        Args:
            e: 発生した例外

        Returns:
            str: ユーザー向け日本語エラーメッセージ
        """
        return "処理内容が長くなりすぎたため停止しました。入力内容を短くするか、担当部署へご連絡ください。"

    def handle_context_window_error(self, e) -> str:
        """コンテキストウィンドウ超過エラー（ContextWindowOverflowException）のメッセージを生成する。

        Args:
            e: 発生した例外

        Returns:
            str: ユーザー向け日本語エラーメッセージ
        """
        return "会話履歴が上限を超えました。最初からやり直すには 'reset' と入力してください。"

    def handle_fare_data_error(self, e) -> str:
        """運賃データ読み込み失敗（FileNotFoundError / Exception）のメッセージを生成する。

        Args:
            e: 発生した例外

        Returns:
            str: ユーザー向け日本語エラーメッセージ
        """
        return "運賃データの読み込みに失敗しました。出発地・目的地をご確認いただくか、運賃を手動で入力してください。"

    def handle_calculation_error(self, e) -> str:
        """運賃計算失敗（Exception）のメッセージを生成する。

        Args:
            e: 発生した例外

        Returns:
            str: ユーザー向け日本語エラーメッセージ
        """
        return "運賃の計算に失敗しました。出発地・目的地・交通手段をご確認いただくか、運賃を手動で入力してください。"

    def handle_file_save_error(self, e) -> str:
        """Excelファイル保存失敗（IOError / PermissionError / Exception）のメッセージを生成する。

        Args:
            e: IOError, PermissionError, またはその他の例外

        Returns:
            str: ユーザー向け日本語エラーメッセージ
        """
        # PermissionErrorを優先してチェックする（IOErrorはPermissionErrorの親クラスのため）
        if isinstance(e, PermissionError):
            return "申請書ファイルへのアクセス権限がありません。担当部署へご連絡ください。"
        if isinstance(e, IOError):
            return "申請書ファイルの出力に失敗しました。しばらくしてから再度お試しいただくか、担当部署へご連絡ください。"
        return "申請書ファイルの保存中に予期しないエラーが発生しました。担当部署へご連絡ください。"

    def handle_validation_error(self, e) -> str:
        """PydanticのValidationErrorをユーザー向け日本語メッセージに変換する。

        Args:
            e: Pydanticが発生させたバリデーションエラー、またはKeyError

        Returns:
            str: ユーザー向け日本語エラーメッセージ（複数エラーは改行区切りで結合）
        """
        if isinstance(e, KeyError):
            return str(e).strip("'")

        if ValidationError is not None and isinstance(e, ValidationError):
            errors = e.errors()
            if not errors:
                return "入力内容にエラーがあります。確認の上、再度入力してください。"
            # 各エラーのmsgを抽出して結合
            messages = [err.get("msg", "入力エラー") for err in errors]
            return "\n".join(messages)

        # ValidationError以外の場合はそのままメッセージを返す
        return str(e) if str(e) else "入力内容にエラーがあります。確認の上、再度入力してください。"

    def handle_keyboard_interrupt(self, e) -> str:
        """ユーザーによる中断（KeyboardInterrupt）のメッセージを生成する。

        Args:
            e: 発生した例外

        Returns:
            str: ユーザー向け日本語メッセージ
        """
        return "処理を中断しました。ご利用ありがとうございました。"

    def handle_loop_limit_error(self, e: LoopLimitError) -> str:
        """LoopLimitError（ループ上限到達）のメッセージを生成する。

        Args:
            e: 発生したLoopLimitError

        Returns:
            str: ユーザー向け日本語エラーメッセージ
        """
        return "処理が長くなりすぎたため停止しました。担当部署へご連絡ください。"

    def handle_runtime_error(self, e) -> str:
        """その他の実行時エラー（RuntimeError）のメッセージを生成する。

        Args:
            e: 発生した例外

        Returns:
            str: ユーザー向け日本語エラーメッセージ
        """
        return "申請処理中にシステムエラーが発生しました。担当部署へご連絡ください。"

    def handle_unexpected_error(self, e) -> str:
        """予期しないエラー（Exception）のメッセージ生成・エスカレーション案内を行う。

        Args:
            e: 発生した例外

        Returns:
            str: エスカレーション案内を含むユーザー向け日本語エラーメッセージ
        """
        return "申請処理中に予期しないエラーが発生しました。担当部署へご連絡ください。"


# ============================================================
# HumanApprovalHook クラス
# ============================================================

class HumanApprovalHook(HookProvider):
    """AG-002/AG-003がTOOL-002を呼び出す前にBeforeToolCallEventを受けて社員確認を挟むフック。

    責務: generate_transport_application/generate_expense_applicationの呼び出し前に
    社員確認（OK/修正/キャンセル）を挟む。ツール中止はevent.cancel_toolにメッセージをセットすることで行う。
    制約:
      - AG-002/AG-003のみに登録する（AG-001には登録しない）
      - event.cancel_tool に文字列をセットしてキャンセル（event.cancel()は存在しない）
    """

    # DD-03: 承認対象ツール名（generate_transport_application/generate_expense_application）
    APPROVAL_REQUIRED_TOOLS = [
        "generate_transport_application",
        "generate_expense_application",
    ]

    def __init__(self):
        pass

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        """HookRegistryにBeforeToolCallEventハンドラーを登録する（HookProviderインタフェース実装）。

        Args:
            registry: Strands AgentsのHookRegistry
            **kwargs: 追加パラメータ（未使用）
        """
        registry.add_callback(BeforeToolCallEvent, self._before_tool_call)

    def _before_tool_call(self, event: BeforeToolCallEvent) -> None:
        """BeforeToolCallEventでツール名を確認し、承認対象ツールのみ社員確認を実施する。

        Args:
            event: BeforeToolCallEvent（全ツール呼び出しで発火するためフィルタリング必須）
        """
        # tool_use辞書からツール名を取得する（R9.8.3準拠）
        tool_name = event.tool_use.get("name", "") if hasattr(event, "tool_use") and event.tool_use else ""
        tool_params = event.tool_use.get("input") or {} if hasattr(event, "tool_use") and event.tool_use else {}

        # 承認対象外のツールはスキップする（BeforeToolCallEventは全ツールで発火するため必須）
        if tool_name not in self.APPROVAL_REQUIRED_TOOLS:
            logger.info("HumanApprovalHook: skipped for tool=%s", tool_name)
            return

        # _approval_callbackを呼び出して社員確認を実施する
        approved, message = self._approval_callback(tool_name=tool_name, tool_params=tool_params)

        if approved:
            logger.info("HumanApprovalHook: approved for tool=%s", tool_name)
            return

        # キャンセルまたは修正: event.cancel_toolにメッセージをセットしてツール実行を中断
        if message == "CANCEL":
            logger.warning("HumanApprovalHook: cancelled for tool=%s", tool_name)
            event.cancel_tool = "申請をキャンセルしました。"
        else:
            logger.warning("HumanApprovalHook: modification requested for tool=%s", tool_name)
            event.cancel_tool = message

    def _approval_callback(self, tool_name: str, tool_params: dict) -> tuple:
        """申請書生成前に社員確認（OK/修正/キャンセル）を求めるコールバック。

        Args:
            tool_name: 呼び出し対象のツール名
            tool_params: ツールに渡されるパラメータ

        Returns:
            tuple:
                (True, "") → OK（ツール実行継続）
                (False, "修正内容") → 修正要望（ツールキャンセル）
                (False, "CANCEL") → キャンセル（ツールキャンセル）
        """
        while True:
            print("\n申請書を生成してよろしいですか？")
            print("1. OK（生成する）")
            print("2. 修正（情報収集に戻る）")
            print("3. キャンセル（申請を終了する）")
            choice = input("選択してください（1/2/3）: ").strip()

            if choice == "1":
                return (True, "")
            elif choice == "2":
                return (False, "修正します。もう一度情報を入力してください。")
            elif choice == "3":
                return (False, "CANCEL")
            else:
                # 無効な入力: 再入力を促す
                print("1、2、3のいずれかを入力してください。")


# ============================================================
# LoopControlHook クラス
# ============================================================

class LoopControlHook(HookProvider):
    """全エージェント（AG-001〜AG-003）のReActループ回数を監視し、上限到達時にLoopLimitErrorを発生させるフック。

    責務: AfterModelCallEventでカウントし、event.exceptionが存在する場合はスキップする。
    BeforeInvocationEventでカウンタをリセットし、AfterInvocationEventでは合計ループ回数をINFOログに出力する。
    制約:
      - max_iterations=10（全エージェント共通・R10準拠）
      - エージェントごとに独立したインスタンスを保持する（カウンタが相互に干渉しない）
      - AfterInvocationEventではカウンタをリセットしない
    """

    def __init__(self, max_iterations: int = 10, agent_name: str = ""):
        """
        Args:
            max_iterations: ReActループの最大繰り返し回数（デフォルト: 10）
            agent_name: エージェント名（LoopLimitErrorのフィールドに使用）
        """
        self.max_iterations = max_iterations
        self.agent_name = agent_name
        # ループカウンタ（初期値: 0）
        self.iteration_count: int = 0

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        """HookRegistryに6つのイベントハンドラーを登録する（HookProviderインタフェース実装）。

        Args:
            registry: Strands AgentsのHookRegistry
            **kwargs: 追加パラメータ（未使用）
        """
        registry.add_callback(BeforeInvocationEvent, self._before_invocation)
        registry.add_callback(BeforeModelCallEvent, self._before_model_call)
        registry.add_callback(AfterModelCallEvent, self._after_model_call)
        registry.add_callback(AfterInvocationEvent, self._after_invocation)
        registry.add_callback(BeforeToolCallEvent, self._before_tool_call_log)
        registry.add_callback(AfterToolCallEvent, self._after_tool_call_log)

    def _before_invocation(self, event: BeforeInvocationEvent) -> None:
        """エージェント呼び出し開始時にループカウンタを0にリセットする。

        Args:
            event: BeforeInvocationEvent
        """
        self.iteration_count = 0
        logger.debug("LoopControlHook: iteration_count reset to 0")

    def _before_model_call(self, event: BeforeModelCallEvent) -> None:
        """LLM呼び出し前にループ回数をINFOレベルでログ出力する。

        Args:
            event: BeforeModelCallEvent
        """
        logger.info("LoopControlHook: starting iteration %d", self.iteration_count + 1)

    def _after_model_call(self, event: AfterModelCallEvent) -> None:
        """LLM呼び出し後にループカウンタをインクリメントし、上限到達を監視する。

        event.exceptionが存在する場合はカウントをスキップする（エラーループ防止）。

        Args:
            event: AfterModelCallEvent

        Raises:
            LoopLimitError: iteration_count >= max_iterationsの場合
        """
        # event.exceptionが存在する場合はカウントをスキップする
        if hasattr(event, "exception") and event.exception is not None:
            return

        self.iteration_count += 1
        logger.debug("LoopControlHook: iteration_count=%d", self.iteration_count)

        # ループ上限チェック
        if self.iteration_count >= self.max_iterations:
            logger.warning(
                "LoopControlHook: max iterations reached (%d) in agent '%s'",
                self.max_iterations,
                self.agent_name,
            )
            raise LoopLimitError(
                current_iteration=self.iteration_count,
                max_iterations=self.max_iterations,
                agent_name=self.agent_name,
            )

    def _after_invocation(self, event: AfterInvocationEvent) -> None:
        """エージェント呼び出し完了後に合計ループ回数をINFOレベルでログ出力する（カウンタリセットなし）。

        Args:
            event: AfterInvocationEvent
        """
        logger.info(
            "LoopControlHook: invocation completed, total iterations=%d",
            self.iteration_count,
        )

    def _before_tool_call_log(self, event: BeforeToolCallEvent) -> None:
        """ツール呼び出し前にツール名をINFOレベルでログ出力する。

        Args:
            event: BeforeToolCallEvent
        """
        tool_name = event.tool_use.get("name", "") if hasattr(event, "tool_use") and event.tool_use else ""
        logger.info("LoopControlHook: tool_call tool=%s", tool_name)

    def _after_tool_call_log(self, event: AfterToolCallEvent) -> None:
        """ツール呼び出し後にツール名をINFOレベルでログ出力する。

        Args:
            event: AfterToolCallEvent
        """
        tool_name = event.tool_use.get("name", "") if hasattr(event, "tool_use") and event.tool_use else ""
        logger.info("LoopControlHook: tool_call_completed tool=%s", tool_name)
