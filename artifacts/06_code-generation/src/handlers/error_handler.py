"""エラーハンドラー

全エージェント・ツールで発生した例外を受け取り、ユーザー向けメッセージ文字列を生成して返す。
ログ出力・セッション状態更新は呼び出し元モジュールが責務を持ち、ErrorHandler 自身は行わない。
"""


class ErrorHandler:
    """例外種別に応じたユーザー向けメッセージを生成して返す共通ハンドラー"""

    def handle_throttling_error(self, e: Exception) -> str:
        return "申し訳ありません。AIサービスへの接続が混雑しています。しばらく時間をおいて再度お試しください。"

    def handle_max_tokens_error(self, e: Exception) -> str:
        return "申し訳ありません。処理できる情報量の上限に達しました。入力内容を短くして再度お試しください。"

    def handle_context_window_error(self, e: Exception) -> str:
        return "申し訳ありません。会話履歴が長くなりすぎました。「reset」と入力してセッションをリセットしてください。"

    def handle_fare_data_error(self, e: Exception) -> str:
        return "申し訳ありません。運賃データの読み込みに失敗しました。システム管理者にご連絡ください。"

    def handle_calculation_error(self, e: Exception) -> str:
        return "申し訳ありません。運賃の計算中にエラーが発生しました。交通費を手動で入力してください。"

    def handle_file_save_error(self, e: Exception) -> str:
        return "申し訳ありません。申請書ファイルの保存に失敗しました。システム管理者にご連絡ください。"

    def handle_validation_error(self, e: Exception) -> str:
        try:
            errors = e.errors()  # type: ignore[attr-defined]
            if errors:
                first = errors[0]
                loc = first.get("loc", ())
                field_name = ".".join(str(part) for part in loc) if loc else "入力項目"
                return f"申請情報に不足している項目があります。{field_name}を入力してください。"
        except Exception:
            pass
        return "申請情報に不足している項目があります。入力内容を確認してください。"

    def handle_keyboard_interrupt(self, e: Exception = None) -> str:  # type: ignore[assignment]
        return "システムを終了します。"

    def handle_loop_limit_error(self, e: Exception) -> str:
        return "処理が複雑になりすぎたため終了します。最初からやり直すには「reset」と入力してください。"

    def handle_runtime_error(self, e: Exception) -> str:
        return "申し訳ありません。処理中にエラーが発生しました。システム管理者にご連絡ください。"

    def handle_unexpected_error(self, e: Exception) -> str:
        return "申し訳ありません。予期しないエラーが発生しました。システム管理者にご連絡ください。"
