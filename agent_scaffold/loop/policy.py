"""循环策略 —— 决定"何时停、出错怎么办"。

把终止逻辑从 agent loop 主体里抽出来，单独可调可测。
这是 Loop Engineering 最容易出问题的地方：该停不停（死循环）、不该停乱停。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LoopPolicy:
    """循环的终止与恢复策略。"""

    max_steps: int = 10               # 单个任务最多迭代多少步（硬上限，防死循环）
    max_consecutive_errors: int = 3   # 连续工具出错多少次就放弃

    def should_stop(self, step: int) -> bool:
        """是否已达最大步数。"""
        return step >= self.max_steps

    def should_abort_on_errors(self, consecutive_errors: int) -> bool:
        """连续错误是否过多，需要中止。"""
        return consecutive_errors >= self.max_consecutive_errors
