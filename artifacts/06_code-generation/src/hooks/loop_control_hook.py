"""LoopControlHookの実装

ReActループのイテレーション回数を監視し、最大回数で強制停止する。
全エージェント（AG-001/AG-002/AG-003）に登録する。
"""
import logging

from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import (
    AfterInvocationEvent,
    AfterModelCallEvent,
    AfterToolCallEvent,
    BeforeInvocationEvent,
    BeforeModelCallEvent,
    BeforeToolCallEvent,
)

from handlers.exceptions import LoopLimitError

__all__ = ["LoopControlHook", "LoopLimitError"]


class LoopControlHook(HookProvider):
    """ReActループのイテレーション回数を監視・制限する暴走防止フック"""

    def __init__(self, max_iterations: int = 30, agent_name: str = "") -> None:
        self._max_iterations = max_iterations
        self._iteration_count = 0
        self._agent_name = agent_name
        self._logger = logging.getLogger(__name__)

    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        registry.add_callback(BeforeInvocationEvent, self._on_before_invocation)
        registry.add_callback(BeforeModelCallEvent, self._on_before_model_call)
        registry.add_callback(AfterModelCallEvent, self._on_after_model_call)
        registry.add_callback(BeforeToolCallEvent, self._on_before_tool_call)
        registry.add_callback(AfterToolCallEvent, self._on_after_tool_call)
        registry.add_callback(AfterInvocationEvent, self._on_after_invocation)

    def _on_before_invocation(self, event: BeforeInvocationEvent) -> None:
        self._iteration_count = 0
        self._logger.info(
            "[LoopControlHook] ループカウンタリセット: agent_name=%s",
            self._agent_name,
        )

    def _on_before_model_call(self, event: BeforeModelCallEvent) -> None:
        self._logger.info(
            "[LoopControlHook] ループ回数: count=%d/%d, agent_name=%s",
            self._iteration_count,
            self._max_iterations,
            self._agent_name,
        )

    def _on_after_model_call(self, event: AfterModelCallEvent) -> None:
        if event.exception is not None:
            return
        self._iteration_count += 1
        if self._iteration_count < self._max_iterations:
            return
        self._logger.warning(
            "[LoopControlHook] ループ上限到達: count=%d/%d, agent_name=%s",
            self._iteration_count,
            self._max_iterations,
            self._agent_name,
        )
        raise LoopLimitError(
            current_iteration=self._iteration_count,
            max_iterations=self._max_iterations,
            agent_name=self._agent_name,
        )

    def _on_before_tool_call(self, event: BeforeToolCallEvent) -> None:
        tool_name = event.tool_use.get("name", "") if event.tool_use else ""
        self._logger.info(
            "[LoopControlHook] ツール呼び出し開始: tool_name=%s, agent_name=%s",
            tool_name,
            self._agent_name,
        )

    def _on_after_tool_call(self, event: AfterToolCallEvent) -> None:
        tool_name = event.tool_use.get("name", "") if event.tool_use else ""
        self._logger.info(
            "[LoopControlHook] ツール呼び出し完了: tool_name=%s, agent_name=%s",
            tool_name,
            self._agent_name,
        )

    def _on_after_invocation(self, event: AfterInvocationEvent) -> None:
        self._logger.info(
            "[LoopControlHook] 呼び出し完了: total_iterations=%d, agent_name=%s",
            self._iteration_count,
            self._agent_name,
        )
