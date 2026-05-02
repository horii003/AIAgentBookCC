from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class LoopLimitError(RuntimeError):
    """Raised when the agent's iteration count exceeds max_iterations."""

    def __init__(self, current_iteration: int, max_iterations: int, agent_name: str = "") -> None:
        self.current_iteration = current_iteration
        self.max_iterations = max_iterations
        self.agent_name = agent_name
        super().__init__(
            f"ループ上限超過: {current_iteration}/{max_iterations} iterations (agent={agent_name!r})"
        )


class LoopControlHook:
    """Hook that limits the number of LLM call iterations per invocation."""

    def __init__(self, max_iterations: int = 10) -> None:
        self._max_iterations = max_iterations
        self._iteration_count = 0

    def register_hooks(self, registry: Any, **kwargs: Any) -> None:
        try:
            from strands.hooks import (
                AfterInvocationEvent,
                AfterModelCallEvent,
                AfterToolCallEvent,
                BeforeInvocationEvent,
                BeforeModelCallEvent,
                BeforeToolCallEvent,
            )
            registry.add_callback(BeforeInvocationEvent, self.on_before_invocation)
            registry.add_callback(BeforeModelCallEvent, self.on_before_model_call)
            registry.add_callback(AfterModelCallEvent, self.on_after_model_call)
            registry.add_callback(BeforeToolCallEvent, self.on_before_tool_call)
            registry.add_callback(AfterToolCallEvent, self.on_after_tool_call)
            registry.add_callback(AfterInvocationEvent, self.on_after_invocation)
        except ImportError:
            pass

    def on_before_invocation(self, event: Any) -> None:
        self._iteration_count = 0
        logger.debug("[OPE-001] LoopControlHook: invocation開始, カウントリセット")

    def on_before_model_call(self, event: Any) -> None:
        self._iteration_count += 1
        logger.debug("[OPE-001] LoopControlHook: model call %d/%d", self._iteration_count, self._max_iterations)
        if self._iteration_count > self._max_iterations:
            agent_name = ""
            try:
                agent_name = event.agent.name or ""
            except AttributeError:
                pass
            raise LoopLimitError(self._iteration_count, self._max_iterations, agent_name)

    def on_after_model_call(self, event: Any) -> None:
        if getattr(event, "exception", None) is not None:
            self._iteration_count -= 1
            logger.debug("[OPE-001] LoopControlHook: model call例外のためカウントデクリメント -> %d", self._iteration_count)

    def on_before_tool_call(self, event: Any) -> None:
        tool_name = getattr(event, "tool_name", "unknown")
        logger.debug("[OPE-001] LoopControlHook: tool呼び出し開始: %s", tool_name)

    def on_after_tool_call(self, event: Any) -> None:
        tool_name = getattr(event, "tool_name", "unknown")
        logger.debug("[OPE-001] LoopControlHook: tool呼び出し完了: %s", tool_name)

    def on_after_invocation(self, event: Any) -> None:
        logger.debug("[OPE-001] LoopControlHook: invocation完了, 総反復数=%d", self._iteration_count)
