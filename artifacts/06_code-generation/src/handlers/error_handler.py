"""エラーハンドリング関連のモジュール

例外からユーザー向けメッセージを生成するスタティックメソッド集。
ログ出力・セッション状態更新は呼び出し元が行う。インスタンス化不要。
"""
from pydantic import ValidationError


class ErrorHandler:
    """例外からユーザー向けメッセージを生成するスタティックメソッド集。

    ログ出力・セッション更新は呼び出し元が行う。インスタンス化不要。
    """

    @staticmethod
    def handle_throttling_error(e: Exception) -> str:
        """APIスロットリングエラー処理: しばらく待つよう案内するメッセージを返す。"""
        return (
            "APIのリクエスト制限に達しました。しばらく待ってから再度お試しください。"
            "繰り返しエラーが発生する場合は、管理部門（経理部）にお問い合わせください。"
        )

    @staticmethod
    def handle_max_tokens_error(e: Exception) -> str:
        """トークン上限超過エラー処理: 入力を短くするよう案内するメッセージを返す。"""
        return "入力内容が長すぎます。入力内容を短くして再度お試しください。"

    @staticmethod
    def handle_context_window_error(e: Exception) -> str:
        """コンテキストウィンドウ超過エラー処理: 再開を案内するメッセージを返す。"""
        return "会話が長くなりすぎました。最初からやり直してください。"

    @staticmethod
    def handle_fare_data_error(e: Exception) -> str:
        """運賃データファイルアクセス失敗処理: リトライ案内メッセージを返す。"""
        return (
            "運賃データの読み込み中にエラーが発生しました。しばらく待ってから再度お試しください。"
            "繰り返しエラーが発生する場合は、管理部門（経理部）にお問い合わせください。"
        )

    @staticmethod
    def handle_calculation_error(e: Exception) -> str:
        """運賃計算処理エラー処理: 管理部門確認依頼メッセージを返す。"""
        return "運賃計算中にエラーが発生しました。管理部門（経理部）にお問い合わせください。"

    @staticmethod
    def handle_file_save_error(e: Exception) -> str:
        """ファイル保存失敗処理: 管理部門案内メッセージを返す。"""
        return (
            "申請書ファイルの保存中にエラーが発生しました。"
            "管理部門（経理部）にお問い合わせください。"
        )

    @staticmethod
    def handle_validation_error(e: Exception) -> str:
        """入力バリデーションエラー処理: 再入力案内メッセージを返す。"""
        detail = _extract_validation_detail(e)
        return f"入力内容に誤りがあります。入力内容をご確認の上、再度入力してください。{detail}"

    @staticmethod
    def handle_keyboard_interrupt(e: Exception) -> str:
        """キーボード割り込み処理: 終了案内メッセージを返す。"""
        return "操作が中断されました。"

    @staticmethod
    def handle_loop_limit_error(e: Exception) -> str:
        """ループ上限到達エラー処理: 再試行案内メッセージを返す。"""
        return "処理の上限回数に達しました。改めて最初からお試しください。"

    @staticmethod
    def handle_runtime_error(e: Exception) -> str:
        """ランタイムエラー処理: 管理部門案内メッセージを返す。"""
        return "処理中に問題が発生しました。管理部門（経理部）にお問い合わせください。"

    @staticmethod
    def handle_unexpected_error(e: Exception) -> str:
        """未分類例外処理: 「処理できませんでした」メッセージを返す。"""
        return "処理できませんでした。管理部門（経理部）にお問い合わせください。"


def _extract_validation_detail(e: Exception) -> str:
    """Pydantic ValidationError から詳細メッセージを抽出するモジュールレベルヘルパー。"""
    try:
        if isinstance(e, ValidationError):
            msgs = [err["msg"] for err in e.errors()]
            return " / ".join(msgs)
        return str(e)
    except Exception:
        return str(e)
