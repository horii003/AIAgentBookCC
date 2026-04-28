"""Unit tests for handlers/error_handler.py and handlers/exceptions.py"""
import pytest
from pydantic import BaseModel, ValidationError, field_validator

from handlers.error_handler import ErrorHandler
from handlers.exceptions import LoopLimitError


# ---- LoopLimitError ----

class TestLoopLimitError:
    def test_fields(self):
        err = LoopLimitError(current_iteration=5, max_iterations=10, agent_name="test_agent")
        assert err.current_iteration == 5
        assert err.max_iterations == 10
        assert err.agent_name == "test_agent"

    def test_is_exception_subclass(self):
        assert issubclass(LoopLimitError, Exception)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(LoopLimitError) as exc_info:
            raise LoopLimitError(3, 10, "agent_x")
        assert exc_info.value.current_iteration == 3

    def test_default_agent_name(self):
        err = LoopLimitError(current_iteration=1, max_iterations=5)
        assert err.agent_name == ""


# ---- Helper: build ValidationError ----

def _make_validation_error() -> ValidationError:
    class _Model(BaseModel):
        name: str

    try:
        _Model(name=None)  # type: ignore
    except ValidationError as e:
        return e
    pytest.fail("Expected ValidationError not raised")


# ---- ErrorHandler ----

class TestErrorHandler:
    def setup_method(self):
        self.handler = ErrorHandler()

    def test_handle_loop_limit_error_message(self):
        err = LoopLimitError(1, 10, "agent")
        msg = self.handler.handle_loop_limit_error(err)
        assert msg == "処理が複雑になりすぎたため終了します。最初からやり直すには「reset」と入力してください。"

    def test_handle_unexpected_error_message(self):
        err = Exception("test")
        msg = self.handler.handle_unexpected_error(err)
        assert msg == "申し訳ありません。予期しないエラーが発生しました。システム管理者にご連絡ください。"

    def test_handle_validation_error_returns_string(self):
        err = _make_validation_error()
        msg = self.handler.handle_validation_error(err)
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_handle_validation_error_contains_field_name(self):
        err = _make_validation_error()
        msg = self.handler.handle_validation_error(err)
        assert "name" in msg or "入力" in msg

    def test_all_methods_return_str(self):
        dummy = Exception("dummy")
        loop_err = LoopLimitError(1, 10, "a")
        ve = _make_validation_error()

        results = [
            self.handler.handle_throttling_error(dummy),
            self.handler.handle_max_tokens_error(dummy),
            self.handler.handle_context_window_error(dummy),
            self.handler.handle_fare_data_error(dummy),
            self.handler.handle_calculation_error(dummy),
            self.handler.handle_file_save_error(dummy),
            self.handler.handle_validation_error(ve),
            self.handler.handle_keyboard_interrupt(),
            self.handler.handle_loop_limit_error(loop_err),
            self.handler.handle_runtime_error(dummy),
            self.handler.handle_unexpected_error(dummy),
        ]
        for msg in results:
            assert isinstance(msg, str), f"Expected str, got {type(msg)}: {msg!r}"

    def test_handle_throttling_error_message(self):
        msg = self.handler.handle_throttling_error(Exception())
        assert "混雑" in msg or "AIサービス" in msg

    def test_handle_keyboard_interrupt_message(self):
        msg = self.handler.handle_keyboard_interrupt()
        assert "終了" in msg
