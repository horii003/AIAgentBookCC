import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from handlers.error_handler import ErrorHandler


class TestErrorHandler:
    def setup_method(self):
        self.handler = ErrorHandler()
        self.dummy = Exception("test")

    def test_handle_throttling_error(self):
        msg = self.handler.handle_throttling_error(self.dummy)
        assert "混雑" in msg

    def test_handle_max_tokens_error(self):
        msg = self.handler.handle_max_tokens_error(self.dummy)
        assert "長すぎ" in msg

    def test_handle_context_window_error(self):
        msg = self.handler.handle_context_window_error(self.dummy)
        assert "やり直し" in msg

    def test_handle_fare_data_error(self):
        msg = self.handler.handle_fare_data_error(self.dummy)
        assert "運賃データ" in msg

    def test_handle_calculation_error(self):
        msg = self.handler.handle_calculation_error(self.dummy)
        assert "運賃計算" in msg

    def test_handle_file_save_error(self):
        msg = self.handler.handle_file_save_error(self.dummy)
        assert "申請書" in msg

    def test_handle_validation_error_generic(self):
        e = Exception("入力が不正です")
        msg = self.handler.handle_validation_error(e)
        assert "入力" in msg
        assert "90日" not in msg

    def test_handle_validation_error_with_90days(self):
        e = Exception("申請期限（経費発生日から90日以内）を超過しています")
        msg = self.handler.handle_validation_error(e)
        assert "90日" in msg

    def test_handle_validation_error_with_deadline(self):
        e = Exception("申請期限超過")
        msg = self.handler.handle_validation_error(e)
        assert "90日" in msg or "申請期限" in msg

    def test_handle_keyboard_interrupt(self):
        msg = self.handler.handle_keyboard_interrupt(self.dummy)
        assert "中断" in msg

    def test_handle_loop_limit_error(self):
        msg = self.handler.handle_loop_limit_error(self.dummy)
        assert "予期" in msg

    def test_handle_runtime_error(self):
        msg = self.handler.handle_runtime_error(self.dummy)
        assert "システムエラー" in msg

    def test_handle_unexpected_error(self):
        msg = self.handler.handle_unexpected_error(self.dummy)
        assert "予期" in msg

    def test_all_methods_return_strings(self):
        methods = [
            self.handler.handle_throttling_error,
            self.handler.handle_max_tokens_error,
            self.handler.handle_context_window_error,
            self.handler.handle_fare_data_error,
            self.handler.handle_calculation_error,
            self.handler.handle_file_save_error,
            self.handler.handle_keyboard_interrupt,
            self.handler.handle_loop_limit_error,
            self.handler.handle_runtime_error,
            self.handler.handle_unexpected_error,
        ]
        for method in methods:
            result = method(self.dummy)
            assert isinstance(result, str)
            assert len(result) > 0
