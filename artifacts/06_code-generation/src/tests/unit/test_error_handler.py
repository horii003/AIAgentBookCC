# 参照: DD-03 ハンドラー詳細設計書
"""handlers/error_handler.py の単体テスト"""
import sys
import os
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from handlers.error_handler import (
    LoopLimitError,
    ErrorHandler,
    HumanApprovalHook,
    LoopControlHook,
)


class TestLoopLimitError:
    """LoopLimitError のテスト"""

    def test_fields_set_correctly(self):
        """LoopLimitErrorに全フィールドが設定されること。"""
        err = LoopLimitError(current_iteration=10, max_iterations=10, agent_name="test_agent")
        assert err.current_iteration == 10
        assert err.max_iterations == 10
        assert err.agent_name == "test_agent"

    def test_is_exception(self):
        """LoopLimitErrorがExceptionのサブクラスであること。"""
        err = LoopLimitError(5, 10, "agent")
        assert isinstance(err, Exception)

    def test_message_contains_info(self):
        """エラーメッセージに反復回数とエージェント名が含まれること。"""
        err = LoopLimitError(10, 10, "orchestrator_agent")
        assert "10" in str(err)
        assert "orchestrator_agent" in str(err)


class TestErrorHandler:
    """ErrorHandler のテスト"""

    def setup_method(self):
        self.handler = ErrorHandler()

    def test_handle_throttling_error(self):
        """handle_throttling_errorが日本語メッセージを返すこと。"""
        msg = self.handler.handle_throttling_error(Exception("throttle"))
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_handle_max_tokens_error(self):
        """handle_max_tokens_errorが日本語メッセージを返すこと。"""
        msg = self.handler.handle_max_tokens_error(Exception())
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_handle_context_window_error(self):
        """handle_context_window_errorが日本語メッセージを返すこと。"""
        msg = self.handler.handle_context_window_error(Exception())
        assert isinstance(msg, str)
        assert "reset" in msg

    def test_handle_fare_data_error(self):
        """handle_fare_data_errorが日本語メッセージを返すこと。"""
        msg = self.handler.handle_fare_data_error(FileNotFoundError())
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_handle_file_save_error_permission(self):
        """PermissionErrorでアクセス権限エラーメッセージを返すこと。"""
        msg = self.handler.handle_file_save_error(PermissionError())
        assert "権限" in msg

    def test_handle_file_save_error_io(self):
        """IOErrorで出力失敗メッセージを返すこと。"""
        msg = self.handler.handle_file_save_error(IOError())
        assert "出力" in msg or "失敗" in msg

    def test_handle_file_save_error_other(self):
        """その他の例外で予期しないエラーメッセージを返すこと。"""
        msg = self.handler.handle_file_save_error(RuntimeError("unexpected"))
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_handle_validation_error_with_pydantic(self):
        """ValidationErrorを渡したとき日本語エラーメッセージを返すこと。"""
        try:
            from pydantic import BaseModel, Field, ValidationError
            class TestModel(BaseModel):
                name: str = Field(..., min_length=1)
            try:
                TestModel(name="")
            except ValidationError as e:
                msg = self.handler.handle_validation_error(e)
                assert isinstance(msg, str)
                assert len(msg) > 0
        except ImportError:
            pytest.skip("pydantic not available")

    def test_handle_validation_error_with_key_error(self):
        """KeyErrorを渡したときメッセージを返すこと。"""
        msg = self.handler.handle_validation_error(KeyError("test_key"))
        assert isinstance(msg, str)

    def test_handle_keyboard_interrupt(self):
        """handle_keyboard_interruptが終了メッセージを返すこと。"""
        msg = self.handler.handle_keyboard_interrupt(KeyboardInterrupt())
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_handle_loop_limit_error(self):
        """handle_loop_limit_errorが停止メッセージを返すこと。"""
        err = LoopLimitError(10, 10, "agent")
        msg = self.handler.handle_loop_limit_error(err)
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_handle_runtime_error(self):
        """handle_runtime_errorがシステムエラーメッセージを返すこと。"""
        msg = self.handler.handle_runtime_error(RuntimeError("runtime"))
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_handle_unexpected_error(self):
        """handle_unexpected_errorがエスカレーションメッセージを返すこと。"""
        msg = self.handler.handle_unexpected_error(Exception("unexpected"))
        assert isinstance(msg, str)
        assert len(msg) > 0


class TestLoopControlHook:
    """LoopControlHook のテスト"""

    def setup_method(self):
        self.hook = LoopControlHook(max_iterations=10, agent_name="test_agent")

    def test_initial_state(self):
        """初期状態でiteration_count=0であること。"""
        assert self.hook.iteration_count == 0
        assert self.hook.max_iterations == 10
        assert self.hook.agent_name == "test_agent"

    def test_before_invocation_resets_counter(self):
        """_before_invocationでカウンタがリセットされること。"""
        self.hook.iteration_count = 5
        event = MagicMock(spec=BeforeInvocationEvent if 'BeforeInvocationEvent' in dir() else object)
        self.hook._before_invocation(event)
        assert self.hook.iteration_count == 0

    def test_after_model_call_increments_counter(self):
        """_after_model_callでカウンタがインクリメントされること（exception=None）。"""
        event = MagicMock()
        event.exception = None
        self.hook._after_model_call(event)
        assert self.hook.iteration_count == 1

    def test_after_model_call_skips_on_exception(self):
        """event.exceptionが存在する場合カウントがスキップされること。"""
        event = MagicMock()
        event.exception = RuntimeError("error")
        self.hook._after_model_call(event)
        assert self.hook.iteration_count == 0  # カウントされないこと

    def test_raises_loop_limit_error_at_max(self):
        """10回目のLLM呼び出しでLoopLimitErrorが発生すること。"""
        event = MagicMock()
        event.exception = None

        # 9回はOK
        for i in range(9):
            self.hook._after_model_call(event)
        assert self.hook.iteration_count == 9

        # 10回目でLoopLimitError
        with pytest.raises(LoopLimitError) as exc_info:
            self.hook._after_model_call(event)
        assert exc_info.value.current_iteration == 10
        assert exc_info.value.max_iterations == 10
        assert exc_info.value.agent_name == "test_agent"

    def test_continues_at_9_stops_at_10(self):
        """9回目は継続し10回目で停止すること（境界値テスト）。"""
        event = MagicMock()
        event.exception = None

        # 9回実行（9回目まではエラーなし）
        for i in range(9):
            self.hook._after_model_call(event)
        assert self.hook.iteration_count == 9

        # 10回目でLoopLimitError
        with pytest.raises(LoopLimitError):
            self.hook._after_model_call(event)

    def test_register_hooks_calls_add_callback(self):
        """register_hooksが6つのイベントにadd_callbackを呼ぶこと。"""
        mock_registry = MagicMock()
        self.hook.register_hooks(mock_registry)
        assert mock_registry.add_callback.call_count == 6

    def test_after_invocation_logs_total(self):
        """_after_invocationで合計ループ回数がログ出力されること（カウンタリセットなし）。"""
        self.hook.iteration_count = 5
        event = MagicMock()
        self.hook._after_invocation(event)
        # カウンタがリセットされないこと
        assert self.hook.iteration_count == 5


class TestHumanApprovalHook:
    """HumanApprovalHook のテスト"""

    def setup_method(self):
        self.hook = HumanApprovalHook()

    def _make_tool_event(self, tool_name: str) -> MagicMock:
        event = MagicMock()
        event.tool_use = {"name": tool_name, "input": {}}
        event.cancel_tool = False
        return event

    def test_skips_non_target_tool(self):
        """対象外ツール（calculate_transport_fare）でスキップされること。"""
        event = self._make_tool_event("calculate_transport_fare")
        # _approval_callbackが呼ばれないことを確認（cancel_toolが変更されないこと）
        self.hook._before_tool_call(event)
        assert event.cancel_tool is False

    def test_cancel_sets_cancel_message(self):
        """キャンセル選択時にevent.cancel_toolにキャンセルメッセージがセットされること。"""
        event = self._make_tool_event("generate_transport_application")
        # _approval_callbackをモックしてキャンセルを返す
        self.hook._approval_callback = MagicMock(return_value=(False, "CANCEL"))
        self.hook._before_tool_call(event)
        assert event.cancel_tool == "申請をキャンセルしました。"

    def test_modification_sets_modification_message(self):
        """修正選択時にevent.cancel_toolに修正メッセージがセットされること。"""
        event = self._make_tool_event("generate_transport_application")
        self.hook._approval_callback = MagicMock(return_value=(False, "修正します。もう一度情報を入力してください。"))
        self.hook._before_tool_call(event)
        assert event.cancel_tool == "修正します。もう一度情報を入力してください。"

    def test_ok_does_not_cancel(self):
        """OK選択時にevent.cancel_toolが変更されないこと。"""
        event = self._make_tool_event("generate_transport_application")
        self.hook._approval_callback = MagicMock(return_value=(True, ""))
        self.hook._before_tool_call(event)
        assert event.cancel_tool is False

    def test_expense_tool_is_target(self):
        """generate_expense_applicationも承認対象であること。"""
        event = self._make_tool_event("generate_expense_application")
        self.hook._approval_callback = MagicMock(return_value=(False, "CANCEL"))
        self.hook._before_tool_call(event)
        assert event.cancel_tool == "申請をキャンセルしました。"

    def test_invalid_input_then_valid(self, monkeypatch):
        """無効な入力（"4"）後に有効入力（"1"）で処理されること。"""
        inputs = iter(["4", "1"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        approved, msg = self.hook._approval_callback("generate_transport_application", {})
        assert approved is True
        assert msg == ""

    def test_register_hooks_calls_add_callback(self):
        """register_hooksがBeforeToolCallEventにadd_callbackを呼ぶこと。"""
        mock_registry = MagicMock()
        self.hook.register_hooks(mock_registry)
        assert mock_registry.add_callback.call_count >= 1
