"""Loop Engineering 层 —— 驱动 Agent 一轮一轮转起来。

  - policy.py  终止条件、最大步数、错误恢复策略（"何时停"）
  - agent.py   agentic loop 本体：observe → think → act → repeat（"怎么转"）
"""

from .policy import LoopPolicy
from .agent import Agent

__all__ = ["LoopPolicy", "Agent"]
