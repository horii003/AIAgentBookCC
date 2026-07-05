"""エラーハンドリング関連のモジュール"""
from typing import Optional


class LoopLimitError(RuntimeError):
    """エージェントReActループの制限エラー

    エージェントのループが最大回数に達した場合に発生する。
    """

    def __init__(self, current_iteration: int, max_iterations: int, agent_name: str):
        self.current_iteration = current_iteration
        self.max_iterations = max_iterations
        self.agent_name = agent_name
        message = (
            f"エージェント '{agent_name}' のループ回数が上限 ({max_iterations}回) に達しました。"
            f"（現在: {current_iteration}回）"
        )
        super().__init__(message)


class ErrorHandler:
    """エラーハンドリングヘルパー関数クラス

    例外オブジェクトを受け取り、ユーザー向け日本語エラーメッセージ文字列を生成して返す。
    ログ出力・セッション状態更新は一切行わない（呼び出し元が実施する）。
    """

    # ============ 共通エラーハンドリングメソッド ============

    @staticmethod
    def handle_keyboard_interrupt(error: Optional[Exception] = None) -> str:
        return "申請処理を中断しました。またのご利用をお待ちしております。"

    @staticmethod
    def handle_loop_limit_error(error: "LoopLimitError") -> str:
        return "処理の繰り返し回数が上限に達しました。しばらく経ってから再度お試しください。"

    @staticmethod
    def handle_validation_error(error: Optional[Exception] = None) -> str:
        return "入力内容に不備があります。必須項目をご確認の上、再度お試しください。"

    @staticmethod
    def handle_runtime_error(error: Optional[Exception] = None) -> str:
        return "申請処理中にエラーが発生しました。担当部門にお問い合わせください。"

    @staticmethod
    def handle_unexpected_error(error: Optional[Exception] = None) -> str:
        return "予期しないエラーが発生しました。担当部門にお問い合わせください。"

    # ============ ドメイン固有エラーハンドリングメソッド ============

    @staticmethod
    def handle_throttling_error(error: Optional[Exception] = None) -> str:
        return "現在、システムへのリクエストが集中しています。しばらく経ってから再度お試しください。"

    @staticmethod
    def handle_max_tokens_error(error: Optional[Exception] = None) -> str:
        return "入力内容が長すぎます。内容を分割して再度お試しください。"

    @staticmethod
    def handle_context_window_error(error: Optional[Exception] = None) -> str:
        return "会話履歴が上限に達しました。'reset' コマンドで最初からやり直してください。"

    @staticmethod
    def handle_fare_data_error(error: Optional[Exception] = None) -> str:
        return "交通費データの読み込みに失敗しました。担当部門にお問い合わせください。"

    @staticmethod
    def handle_calculation_error(error: Optional[Exception] = None) -> str:
        return "交通費の計算中にエラーが発生しました。手動で金額を入力してください。"

    @staticmethod
    def handle_file_save_error(error: Optional[Exception] = None) -> str:
        return "申請書ファイルの保存に失敗しました。担当部門にお問い合わせください。"
