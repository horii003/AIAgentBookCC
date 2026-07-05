"""ErrorHandlerの単体テスト"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from pydantic import BaseModel, ValidationError
from handlers.error_handler import LoopLimitError, ErrorHandler


class TestLoopLimitError:
    def test_初期化フィールドが保持される(self):
        error = LoopLimitError(current_iteration=10, max_iterations=10, agent_name="reception_agent")
        assert error.current_iteration == 10
        assert error.max_iterations == 10
        assert error.agent_name == "reception_agent"

    def test_メッセージにエージェント名とループ回数が含まれる(self):
        error = LoopLimitError(current_iteration=5, max_iterations=10, agent_name="AG-002")
        msg = str(error)
        assert "AG-002" in msg
        assert "10" in msg

    def test_RuntimeErrorのサブクラスである(self):
        error = LoopLimitError(current_iteration=1, max_iterations=5, agent_name="agent")
        assert isinstance(error, RuntimeError)


class TestErrorHandler:
    def test_handle_keyboard_interruptが文字列を返す(self):
        result = ErrorHandler.handle_keyboard_interrupt()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_handle_keyboard_interrupt_例外引数あり(self):
        result = ErrorHandler.handle_keyboard_interrupt(KeyboardInterrupt())
        assert isinstance(result, str)

    def test_handle_loop_limit_errorが文字列を返す(self):
        error = LoopLimitError(current_iteration=10, max_iterations=10, agent_name="test_agent")
        result = ErrorHandler.handle_loop_limit_error(error)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_handle_validation_errorが文字列を返す(self):
        class _M(BaseModel):
            name: str
        try:
            _M(name=123)
        except Exception:
            pass
        result = ErrorHandler.handle_validation_error()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_handle_runtime_errorが文字列を返す(self):
        result = ErrorHandler.handle_runtime_error(RuntimeError("実行時エラー"))
        assert isinstance(result, str)

    def test_handle_unexpected_errorが文字列を返す(self):
        result = ErrorHandler.handle_unexpected_error(Exception("何らかのエラー"))
        assert isinstance(result, str)

    def test_handle_throttling_errorが文字列を返す(self):
        result = ErrorHandler.handle_throttling_error()
        assert isinstance(result, str)

    def test_handle_max_tokens_errorが文字列を返す(self):
        result = ErrorHandler.handle_max_tokens_error()
        assert isinstance(result, str)

    def test_handle_context_window_errorが文字列を返す(self):
        result = ErrorHandler.handle_context_window_error()
        assert isinstance(result, str)

    def test_handle_fare_data_errorが文字列を返す(self):
        result = ErrorHandler.handle_fare_data_error(FileNotFoundError("data.json"))
        assert isinstance(result, str)

    def test_handle_calculation_errorが文字列を返す(self):
        result = ErrorHandler.handle_calculation_error(Exception("計算エラー"))
        assert isinstance(result, str)

    def test_handle_file_save_errorがIOErrorで文字列を返す(self):
        result = ErrorHandler.handle_file_save_error(IOError("書き込み失敗"))
        assert isinstance(result, str)

    def test_handle_file_save_errorがPermissionErrorで文字列を返す(self):
        result = ErrorHandler.handle_file_save_error(PermissionError("権限なし"))
        assert isinstance(result, str)

    def test_引数Noneでも動作する(self):
        assert isinstance(ErrorHandler.handle_keyboard_interrupt(None), str)
        assert isinstance(ErrorHandler.handle_runtime_error(None), str)
        assert isinstance(ErrorHandler.handle_unexpected_error(None), str)
