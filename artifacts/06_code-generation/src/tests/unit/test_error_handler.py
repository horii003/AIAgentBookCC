"""error_handler.py / exceptions.py の単体テスト"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pytest
from pydantic import BaseModel, Field, ValidationError

from handlers.exceptions import LoopLimitError
from handlers.error_handler import ErrorHandler


class TestLoopLimitError:
    def test_フィールドが正しく設定される(self):
        e = LoopLimitError(current_iteration=5, max_iterations=10, agent_name="test_agent")
        assert e.current_iteration == 5
        assert e.max_iterations == 10
        assert e.agent_name == "test_agent"

    def test_Exceptionのサブクラスである(self):
        e = LoopLimitError(1, 10, "agent")
        assert isinstance(e, Exception)

    def test_メッセージが含まれる(self):
        e = LoopLimitError(3, 10, "my_agent")
        assert "my_agent" in str(e)
        assert "3" in str(e)
        assert "10" in str(e)


class TestErrorHandler:
    def setup_method(self):
        self.handler = ErrorHandler()

    def test_handle_loop_limit_error_メッセージ確認(self):
        e = LoopLimitError(5, 10, "agent")
        result = self.handler.handle_loop_limit_error(e)
        assert result == "処理が複雑すぎるため終了します。"

    def test_handle_unexpected_error_メッセージ確認(self):
        e = Exception("test")
        result = self.handler.handle_unexpected_error(e)
        assert result == "申し訳ありません。予期しないエラーが発生しました。システム管理者にご連絡ください。"

    def test_handle_validation_error_ValidationErrorから文字列返却(self):
        class _M(BaseModel):
            name: str = Field(..., min_length=1)

        try:
            _M(name="")
        except ValidationError as e:
            result = self.handler.handle_validation_error(e)
            assert isinstance(result, str)
            assert len(result) > 0

    def test_handle_throttling_error_文字列を返す(self):
        result = self.handler.handle_throttling_error(Exception())
        assert isinstance(result, str)
        assert len(result) > 0

    def test_handle_max_tokens_error_文字列を返す(self):
        result = self.handler.handle_max_tokens_error(Exception())
        assert isinstance(result, str)

    def test_handle_context_window_error_文字列を返す(self):
        result = self.handler.handle_context_window_error(Exception())
        assert isinstance(result, str)

    def test_handle_fare_data_error_文字列を返す(self):
        result = self.handler.handle_fare_data_error(Exception())
        assert isinstance(result, str)

    def test_handle_calculation_error_文字列を返す(self):
        result = self.handler.handle_calculation_error(Exception())
        assert isinstance(result, str)

    def test_handle_file_save_error_文字列を返す(self):
        result = self.handler.handle_file_save_error(Exception())
        assert isinstance(result, str)

    def test_handle_keyboard_interrupt_文字列を返す(self):
        result = self.handler.handle_keyboard_interrupt()
        assert isinstance(result, str)
        assert result == "処理を中断しました。ご利用ありがとうございました。"

    def test_handle_runtime_error_文字列を返す(self):
        result = self.handler.handle_runtime_error(RuntimeError("test"))
        assert isinstance(result, str)
