"""error_handler.py の単体テスト"""
import pytest
from pydantic import BaseModel, ValidationError, field_validator

from handlers.error_handler import ErrorHandler


# バリデーションエラー生成用ヘルパーモデル
class _SampleModel(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("名前が空です")
        return v


def _make_validation_error() -> ValidationError:
    try:
        _SampleModel(name="")
    except ValidationError as e:
        return e
    raise AssertionError("ValidationError が発生しませんでした")


class TestErrorHandler:
    def test_handle_throttling_error_returns_str(self):
        """handle_throttling_error が str を返すこと"""
        result = ErrorHandler.handle_throttling_error(Exception("throttle"))
        assert isinstance(result, str)
        assert len(result) > 0

    def test_handle_max_tokens_error_returns_str(self):
        """handle_max_tokens_error が str を返すこと"""
        result = ErrorHandler.handle_max_tokens_error(Exception("max tokens"))
        assert isinstance(result, str)

    def test_handle_context_window_error_returns_str(self):
        """handle_context_window_error が str を返すこと"""
        result = ErrorHandler.handle_context_window_error(Exception("context"))
        assert isinstance(result, str)

    def test_handle_fare_data_error_returns_str(self):
        """handle_fare_data_error が str を返すこと"""
        result = ErrorHandler.handle_fare_data_error(FileNotFoundError("not found"))
        assert isinstance(result, str)

    def test_handle_calculation_error_returns_str(self):
        """handle_calculation_error が str を返すこと"""
        result = ErrorHandler.handle_calculation_error(Exception("calc error"))
        assert isinstance(result, str)

    def test_handle_file_save_error_returns_str(self):
        """handle_file_save_error が str を返すこと"""
        result = ErrorHandler.handle_file_save_error(IOError("io error"))
        assert isinstance(result, str)

    def test_handle_validation_error_contains_field_detail(self):
        """handle_validation_error がフィールド名を含む日本語メッセージを返すこと"""
        e = _make_validation_error()
        result = ErrorHandler.handle_validation_error(e)
        assert isinstance(result, str)
        assert "入力内容に誤りがあります" in result
        assert "名前が空です" in result

    def test_handle_keyboard_interrupt_returns_str(self):
        """handle_keyboard_interrupt が str を返すこと"""
        result = ErrorHandler.handle_keyboard_interrupt(KeyboardInterrupt())
        assert isinstance(result, str)

    def test_handle_loop_limit_error_returns_str(self):
        """handle_loop_limit_error が str を返すこと"""
        result = ErrorHandler.handle_loop_limit_error(RuntimeError("loop limit"))
        assert isinstance(result, str)
        assert len(result) > 0

    def test_handle_runtime_error_returns_str(self):
        """handle_runtime_error が str を返すこと"""
        result = ErrorHandler.handle_runtime_error(RuntimeError("runtime"))
        assert isinstance(result, str)

    def test_handle_unexpected_error_returns_str(self):
        """handle_unexpected_error が str を返すこと"""
        result = ErrorHandler.handle_unexpected_error(Exception("unexpected"))
        assert isinstance(result, str)

    def test_no_exception_raised_with_none_like_input(self):
        """各メソッドがNone相当の引数でも例外を発生させないこと"""
        assert ErrorHandler.handle_throttling_error(Exception()) is not None
        assert ErrorHandler.handle_max_tokens_error(Exception()) is not None
        assert ErrorHandler.handle_context_window_error(Exception()) is not None
        assert ErrorHandler.handle_fare_data_error(Exception()) is not None
        assert ErrorHandler.handle_calculation_error(Exception()) is not None
        assert ErrorHandler.handle_file_save_error(Exception()) is not None
        assert ErrorHandler.handle_keyboard_interrupt(Exception()) is not None
        assert ErrorHandler.handle_loop_limit_error(Exception()) is not None
        assert ErrorHandler.handle_runtime_error(Exception()) is not None
        assert ErrorHandler.handle_unexpected_error(Exception()) is not None
