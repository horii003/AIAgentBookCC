"""エラーハンドリングモジュール

ユーザー向けメッセージ文字列を生成して返すクラスを定義する。
ログ出力は呼び出し元（各エージェント・各ツール）の責務であり、
ErrorHandler 自身はログ出力を行わない。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from handlers.exceptions import LoopLimitError


class ErrorHandler:
    """エラーハンドラークラス

    例外オブジェクトを受け取り、ユーザー向けメッセージ文字列を生成して返す。
    インスタンス変数・ログ出力は持たない。
    """

    def handle_throttling_error(self, e: Exception) -> str:
        return "申し訳ありません。APIの利用制限に達しました。しばらく時間をおいて再度お試しください。"

    def handle_max_tokens_error(self, e: Exception) -> str:
        return "申し訳ありません。処理できるテキスト量の上限に達しました。入力内容を分割してお試しください。"

    def handle_context_window_error(self, e: Exception) -> str:
        return "申し訳ありません。会話が長くなりすぎました。最初からやり直してください。"

    def handle_fare_data_error(self, e: Exception) -> str:
        return "申し訳ありません。運賃データの読み込みに失敗しました。システム管理者にご連絡ください。"

    def handle_calculation_error(self, e: Exception) -> str:
        return "申し訳ありません。運賃の計算に失敗しました。交通費を手動で入力してください。"

    def handle_file_save_error(self, e: Exception) -> str:
        return "申し訳ありません。ファイルの生成に失敗しました。システム管理者にご連絡ください。"

    def handle_validation_error(self, e: Exception) -> str:
        """Pydantic ValidationError からユーザー向けメッセージを生成して返す。"""
        try:
            errors = e.errors()  # type: ignore[attr-defined]
            messages = []
            for err in errors:
                msg = err.get("msg", str(err))
                messages.append(msg)
            return "\n".join(messages) if messages else str(e)
        except AttributeError:
            return str(e)

    def handle_keyboard_interrupt(self, e: Exception | None = None) -> str:
        return "処理を中断しました。ご利用ありがとうございました。"

    def handle_loop_limit_error(self, e: "LoopLimitError") -> str:
        return "処理が複雑すぎるため終了します。"

    def handle_runtime_error(self, e: Exception) -> str:
        return "申し訳ありません。処理中にエラーが発生しました。システム管理者にご連絡ください。"

    def handle_unexpected_error(self, e: Exception) -> str:
        return "申し訳ありません。予期しないエラーが発生しました。システム管理者にご連絡ください。"
