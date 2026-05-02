class ErrorHandler:
    """Stateless error handler. All methods return Japanese user-facing messages."""

    def handle_throttling_error(self, e: Exception) -> str:
        return "申し訳ありません。現在システムが混雑しています。しばらく経ってから再度お試しください。"

    def handle_max_tokens_error(self, e: Exception) -> str:
        return "申し訳ありません。入力内容が長すぎます。内容を短くして再度お試しください。"

    def handle_context_window_error(self, e: Exception) -> str:
        return "申し訳ありません。会話が長くなりすぎました。最初からやり直してください。"

    def handle_fare_data_error(self, e: Exception) -> str:
        return "申し訳ありません。運賃データの読み込みに失敗しました。担当部門（管理部）にお問い合わせください。"

    def handle_calculation_error(self, e: Exception) -> str:
        return "申し訳ありません。運賃計算中にエラーが発生しました。区間情報を確認して再度お試しください。"

    def handle_file_save_error(self, e: Exception) -> str:
        return "申し訳ありません。申請書の保存に失敗しました。担当部門（管理部）にお問い合わせください。"

    def handle_validation_error(self, e: Exception) -> str:
        msg = str(e)
        if "90日" in msg or "申請期限" in msg:
            return "申請期限（経費発生日から90日以内）を超過しています。担当部門にご確認ください。"
        return "入力内容に誤りがあります。入力内容をご確認のうえ、再度お試しください。"

    def handle_keyboard_interrupt(self, e: Exception) -> str:
        return "申請フローを中断しました。またいつでもご利用ください。"

    def handle_loop_limit_error(self, e: Exception) -> str:
        return "申し訳ありません。予期しないエラーが発生しました。担当部門（管理部）にお問い合わせいただくか、最初からやり直してください。"

    def handle_runtime_error(self, e: Exception) -> str:
        return "申し訳ありません。システムエラーが発生しました。しばらく経ってから再度お試しください。"

    def handle_unexpected_error(self, e: Exception) -> str:
        return "申し訳ありません。予期しないエラーが発生しました。担当部門（管理部）にお問い合わせいただくか、最初からやり直してください。"
