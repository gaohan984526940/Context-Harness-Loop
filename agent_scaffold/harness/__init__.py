"""Harness Engineering 层 —— 模型周围的支架。

模型本身只会"输入 token → 输出 token"。要让它真正做事，需要：
  - llm.py           模型客户端（OpenAI 兼容，对接 DeepSeek）—— 模型的"嘴"
  - tools.py         工具注册表与执行分发 —— 模型的"手"
  - builtin_tools.py 开箱即用的几个工具
  - guardrails.py    危险操作拦截 —— 安全带
"""

from .llm import LLMClient, LLMResponse
from .tools import ToolRegistry, tool, ToolCall, ToolResult
from .guardrails import Guardrails

__all__ = [
    "LLMClient",
    "LLMResponse",
    "ToolRegistry",
    "tool",
    "ToolCall",
    "ToolResult",
    "Guardrails",
]
