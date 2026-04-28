"""HookProvider 実装

LoopControlHook: ReActループの最大回数を制御する。
HumanApprovalHook: TOOL-002呼び出し前に利用者確認を取得する。
"""
from __future__ import annotations

import logging
from datetime import datetime
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

from handlers.exceptions import LoopLimitError

logger = logging.getLogger(__name__)


class LoopControlHook(HookProvider):
    """ReActループの最大回数を制御するフック"""

    def __init__(self, max_iterations: int = 10) -> None:
        self.max_iterations = max_iterations
        self._iteration_count: int = 0

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        registry.add_callback(BeforeInvocationEvent, self._handle_before_invocation)
        registry.add_callback(BeforeModelCallEvent, self._handle_before_model_call)
        registry.add_callback(AfterModelCallEvent, self._handle_after_model_call)
        registry.add_callback(AfterInvocationEvent, self._handle_after_invocation)
        registry.add_callback(BeforeToolCallEvent, self._handle_before_tool_call)
        registry.add_callback(AfterToolCallEvent, self._handle_after_tool_call)

    def _reset_counter(self) -> None:
        self._iteration_count = 0

    def _increment_and_check(self, agent_name: str) -> None:
        self._iteration_count += 1
        if self._iteration_count >= self.max_iterations:
            logger.warning(
                "[LoopControlHook] Loop limit reached: "
                "iteration_count=%d, max_iterations=%d, agent_name=%s",
                self._iteration_count,
                self.max_iterations,
                agent_name,
            )
            raise LoopLimitError(
                current_iteration=self._iteration_count,
                max_iterations=self.max_iterations,
                agent_name=agent_name,
            )

    def _handle_before_invocation(self, event: BeforeInvocationEvent) -> None:
        self._reset_counter()
        agent_name = getattr(event, "agent_name", "unknown")
        logger.info("[LoopControlHook] BeforeInvocation: agent=%s, counter reset to 0", agent_name)

    def _handle_before_model_call(self, event: BeforeModelCallEvent) -> None:
        logger.debug(
            "[LoopControlHook] BeforeModelCall: iteration=%d", self._iteration_count
        )

    def _handle_after_model_call(self, event: AfterModelCallEvent) -> None:
        if getattr(event, "exception", None) is not None:
            return
        agent_name = getattr(event, "agent_name", "unknown")
        self._increment_and_check(agent_name)

    def _handle_after_invocation(self, event: AfterInvocationEvent) -> None:
        agent_name = getattr(event, "agent_name", "unknown")
        logger.info(
            "[LoopControlHook] AfterInvocation: agent=%s, total_iterations=%d",
            agent_name,
            self._iteration_count,
        )

    def _handle_before_tool_call(self, event: BeforeToolCallEvent) -> None:
        tool_name = getattr(event, "tool_name", "unknown")
        logger.debug("[LoopControlHook] BeforeToolCall: tool=%s", tool_name)

    def _handle_after_tool_call(self, event: AfterToolCallEvent) -> None:
        tool_name = getattr(event, "tool_name", "unknown")
        logger.debug("[LoopControlHook] AfterToolCall: tool=%s", tool_name)


class HumanApprovalHook(HookProvider):
    """TOOL-002呼び出し前に利用者確認（OK/修正/キャンセル）を取得するフック"""

    def __init__(self) -> None:
        self._approval_tool_names: set[str] = {
            "generate_travel_expense_form",
            "generate_expense_form",
        }

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        registry.add_callback(BeforeToolCallEvent, self._handle_before_tool_call)

    def _handle_before_tool_call(self, event: BeforeToolCallEvent) -> None:
        tool_name = getattr(event, "tool_name", "")
        if tool_name not in self._approval_tool_names:
            logger.info("[HumanApprovalHook] Skipped: tool_name=%s", tool_name)
            return

        logger.info("[HumanApprovalHook] Waiting for approval: tool_name=%s", tool_name)
        tool_params = getattr(event, "tool_params", {})
        approved, detail = self._request_approval(tool_name, tool_params)

        if approved:
            return

        if detail == "CANCEL":
            event.cancel_tool = "申請をキャンセルしました。"
        else:
            event.cancel_tool = detail

        logger.info(
            "[HumanApprovalHook] BeforeToolCallEvent: tool_name=%s, selection=%s",
            tool_name,
            "キャンセル" if detail == "CANCEL" else "修正",
        )

    def _request_approval(
        self, tool_name: str, tool_params: dict
    ) -> tuple[bool, str]:
        """利用者へ確認メッセージを提示し、OK/修正/キャンセルの選択を取得する。

        Returns:
            (True, ""): OK
            (False, "CANCEL"): キャンセル
            (False, 修正内容文字列): 修正
        """
        print(
            "申請書を生成してよろしいですか？\n"
            "OK・修正・キャンセルのいずれかを入力してください。"
        )
        while True:
            try:
                user_input = input().strip().lower()
            except EOFError:
                self._log_approval(tool_name, "キャンセル", datetime.now().isoformat())
                return False, "CANCEL"

            if user_input == "ok":
                self._log_approval(tool_name, "ok", datetime.now().isoformat())
                return True, ""
            elif user_input == "修正":
                print("修正内容を入力してください。")
                try:
                    revision = input().strip()
                except EOFError:
                    self._log_approval(tool_name, "キャンセル", datetime.now().isoformat())
                    return False, "CANCEL"
                self._log_approval(tool_name, "修正", datetime.now().isoformat())
                return False, revision
            elif user_input == "キャンセル":
                self._log_approval(tool_name, "キャンセル", datetime.now().isoformat())
                return False, "CANCEL"
            else:
                print("OK・修正・キャンセルのいずれかで入力してください。")

    def _log_approval(self, tool_name: str, selection: str, timestamp: str) -> None:
        logger.info(
            "[HumanApprovalHook] Approval result: tool_name=%s, selection=%s, timestamp=%s",
            tool_name,
            selection,
            timestamp,
        )
