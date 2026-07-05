"""ReActループ制御フック

エージェントのReActループの最大回数を制御し、
ループの状態を表示するフック。
"""
import logging
from typing import Any

from strands.hooks import (
    AfterInvocationEvent,
    AfterModelCallEvent,
    AfterToolCallEvent,
    BeforeInvocationEvent,
    BeforeModelCallEvent,
    BeforeToolCallEvent,
    HookProvider,
    HookRegistry,
)

from handlers.error_handler import LoopLimitError

_logger = logging.getLogger(__name__)


class LoopControlHook(HookProvider):
    """ReActループの最大回数を制御するフック

    BeforeInvocationEvent でカウンターを0にリセットし、AfterModelCallEvent でインクリメントする。
    max_iterations を超えた場合に LoopLimitError を raise する。
    """

    def __init__(self, max_iterations: int = 10, agent_name: str = "Agent"):
        self.max_iterations = max_iterations
        self.agent_name = agent_name
        self.iteration_count = 0

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        registry.add_callback(BeforeInvocationEvent, self.on_before_invocation)
        registry.add_callback(BeforeModelCallEvent, self.on_before_model_call)
        registry.add_callback(AfterModelCallEvent, self.on_after_model_call)
        registry.add_callback(BeforeToolCallEvent, self.on_before_tool_call)
        registry.add_callback(AfterToolCallEvent, self.on_after_tool_call)
        registry.add_callback(AfterInvocationEvent, self.on_after_invocation)

    def on_before_invocation(self, event: BeforeInvocationEvent) -> None:
        self.iteration_count = 0
        _logger.info("LoopControlHook: 呼び出し開始 agent=%s", self.agent_name)

    def on_before_model_call(self, event: BeforeModelCallEvent) -> None:
        _logger.info(
            "LoopControlHook: iteration=%d/%d agent=%s",
            self.iteration_count,
            self.max_iterations,
            self.agent_name,
        )

    def on_after_model_call(self, event: AfterModelCallEvent) -> None:
        if event.exception is not None:
            return
        self.iteration_count += 1
        if self.iteration_count > self.max_iterations:
            _logger.warning(
                "LoopControlHook: 上限超過 iteration_count=%d max_iterations=%d",
                self.iteration_count,
                self.max_iterations,
            )
            raise LoopLimitError(
                current_iteration=self.iteration_count,
                max_iterations=self.max_iterations,
                agent_name=self.agent_name,
            )
        _logger.info(
            "LoopControlHook: 反復カウント更新 count=%d/%d",
            self.iteration_count,
            self.max_iterations,
        )

    def on_before_tool_call(self, event: BeforeToolCallEvent) -> None:
        tool_name = self._get_tool_name(event)
        _logger.info("LoopControlHook: ツール呼び出し開始 tool=%s", tool_name)

    def on_after_tool_call(self, event: AfterToolCallEvent) -> None:
        tool_name = self._get_tool_name(event)
        _logger.info("LoopControlHook: ツール呼び出し完了 tool=%s", tool_name)

    def on_after_invocation(self, event: AfterInvocationEvent) -> None:
        _logger.info(
            "LoopControlHook: 呼び出し完了 合計%dループ agent=%s",
            self.iteration_count,
            self.agent_name,
        )

    def _get_tool_name(self, event) -> str:
        return event.tool_use["name"] if event.tool_use else "unknown"
