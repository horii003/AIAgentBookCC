"""カスタム例外クラスの定義"""


class LoopLimitError(Exception):
    """エージェントReActループの上限到達エラー"""

    def __init__(self, current_iteration: int, max_iterations: int, agent_name: str) -> None:
        self.current_iteration = current_iteration
        self.max_iterations = max_iterations
        self.agent_name = agent_name
        super().__init__(
            f"ループ上限到達: agent={agent_name}, "
            f"current={current_iteration}, max={max_iterations}"
        )
