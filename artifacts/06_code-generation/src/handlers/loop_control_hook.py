"""ReActループ制御フック

エージェントのReActループの最大回数を制御し、
ループの状態を表示するフック。
"""
import logging
from typing import Any

from strands.hooks import (
    HookProvider,
    HookRegistry,
    BeforeInvocationEvent,
    AfterModelCallEvent,
    BeforeModelCallEvent,
    AfterInvocationEvent,
    BeforeToolCallEvent,
    AfterToolCallEvent,
)

logger = logging.getLogger("handlers.loop_control_hook")


class LoopLimitError(Exception):
    """ReActループ上限到達時に発生するカスタム例外。"""

    def __init__(self, current_iteration: int, max_iterations: int, agent_name: str) -> None:
        self.current_iteration = current_iteration
        self.max_iterations = max_iterations
        self.agent_name = agent_name
        super().__init__(
            f"ReActループの上限（{max_iterations}回）に達しました。"
            f"エージェント: {agent_name}, 現在のループ回数: {current_iteration}"
        )


class LoopControlHook(HookProvider):
    """ReActループ回数を監視し上限到達時にループを強制停止するフック。"""

    def __init__(self, max_iterations: int, agent_name: str) -> None:
        self.max_iterations = max_iterations
        self.agent_name = agent_name
        self._loop_count: int = 0

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        """フックの登録"""
        registry.add_callback(BeforeInvocationEvent, self._before_invocation_handler)
        registry.add_callback(BeforeModelCallEvent, self._before_model_call_handler)
        registry.add_callback(AfterModelCallEvent, self._after_model_call_handler)
        registry.add_callback(BeforeToolCallEvent, self._before_tool_call_handler)
        registry.add_callback(AfterToolCallEvent, self._after_tool_call_handler)
        registry.add_callback(AfterInvocationEvent, self._after_invocation_handler)

    def _before_invocation_handler(self, event: BeforeInvocationEvent) -> None:
        """BeforeInvocationEvent ハンドラー: ループカウンタを 0 にリセットする。"""
        self._loop_count = 0
        logger.info(
            f"エージェント呼び出し開始: ループカウンタをリセット"
            f" (エージェント={self.agent_name}, 上限={self.max_iterations})"
        )

    def _before_model_call_handler(self, event: BeforeModelCallEvent) -> None:
        """BeforeModelCallEvent ハンドラー: ループ回数をINFOログ出力する。"""
        logger.info(
            f"LLM 呼び出し開始 (ループ={self._loop_count}, エージェント={self.agent_name})"
        )

    def _after_model_call_handler(self, event: AfterModelCallEvent) -> None:
        """AfterModelCallEvent ハンドラー: ループカウンタをインクリメントし上限監視する。"""
        if getattr(event, "exception", None) is not None:
            return

        self._loop_count += 1
        logger.info(
            f"LLM 呼び出し完了: ループ={self._loop_count}/{self.max_iterations}"
            f" (エージェント={self.agent_name})"
        )

        if self._loop_count >= self.max_iterations:
            logger.warning(
                f"ループ上限に達しました"
                f" (ループ={self._loop_count}, 上限={self.max_iterations},"
                f" エージェント={self.agent_name})"
            )
            raise LoopLimitError(
                current_iteration=self._loop_count,
                max_iterations=self.max_iterations,
                agent_name=self.agent_name,
            )

    def _before_tool_call_handler(self, event: BeforeToolCallEvent) -> None:
        """BeforeToolCallEvent ハンドラー: ツール名をINFOログ出力する。"""
        tool_name = getattr(event, "tool_name", "unknown")
        logger.info(
            f"ツール呼び出し開始 (ツール名={tool_name}, エージェント={self.agent_name})"
        )

    def _after_tool_call_handler(self, event: AfterToolCallEvent) -> None:
        """AfterToolCallEvent ハンドラー: ツール名をINFOログ出力する。"""
        tool_name = getattr(event, "tool_name", "unknown")
        logger.info(
            f"ツール呼び出し完了 (ツール名={tool_name}, エージェント={self.agent_name})"
        )

    def _after_invocation_handler(self, event: AfterInvocationEvent) -> None:
        """AfterInvocationEvent ハンドラー: 合計ループ回数をINFOログ出力する（リセットは行わない）。"""
        logger.info(
            f"エージェント呼び出し完了: 合計ループ回数={self._loop_count}"
            f" (エージェント={self.agent_name})"
        )

    @property
    def loop_count(self) -> int:
        """現在のループカウンタを返す。"""
        return self._loop_count
