"""上下文组装器 —— Context 层的出口。

把【system prompt + 记忆历史 + 工具定义】组装成一次 LLM 请求所需的
messages 与 tools。这是"喂给模型什么"的唯一收口点。
"""

from __future__ import annotations

from typing import Any

from .memory import Memory
from .message import Message


class ContextBuilder:
    """根据 system prompt 与记忆，构建发给 LLM 的最终上下文。"""

    def __init__(self, system_prompt: str) -> None:
        self._system_prompt = system_prompt

    def build_messages(self, memory: Memory) -> list[dict[str, Any]]:
        """组装 messages：system 置顶 + 历史快照。

        注意 system 由 builder 注入，不存进 memory，保证它永远在最前且不被裁剪逻辑误伤。
        """
        messages: list[dict[str, Any]] = [
            Message.system(self._system_prompt).to_openai()
        ]
        for msg in memory.snapshot():
            messages.append(msg.to_openai())
        return messages
