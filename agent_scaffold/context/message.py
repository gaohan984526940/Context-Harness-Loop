"""消息数据结构 —— 不可变。

Context 层流转的最小单位。所有"修改"都返回新对象，绝不原地改。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass(frozen=True)
class Message:
    """一条对话消息。frozen=True —— 不可变，符合 immutability 准则。

    字段对齐 OpenAI 兼容协议：
      - role/content        基本字段
      - tool_calls          assistant 发起的工具调用（OpenAI 原始结构，原样透传）
      - tool_call_id/name   role=tool 的结果，回填给哪个调用
    """

    role: Role
    content: str | None = None
    tool_calls: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    tool_call_id: str | None = None
    name: str | None = None

    def to_openai(self) -> dict[str, Any]:
        """转成 OpenAI 兼容接口要的 dict。只放有值的字段。"""
        msg: dict[str, Any] = {"role": self.role.value}
        if self.content is not None:
            msg["content"] = self.content
        if self.tool_calls:
            msg["tool_calls"] = list(self.tool_calls)
        if self.tool_call_id is not None:
            msg["tool_call_id"] = self.tool_call_id
        if self.name is not None:
            msg["name"] = self.name
        return msg

    # --- 便捷构造器，全部返回新对象 ---

    @staticmethod
    def system(content: str) -> "Message":
        return Message(role=Role.SYSTEM, content=content)

    @staticmethod
    def user(content: str) -> "Message":
        return Message(role=Role.USER, content=content)

    @staticmethod
    def assistant(content: str | None, tool_calls: tuple[dict[str, Any], ...] = ()) -> "Message":
        return Message(role=Role.ASSISTANT, content=content, tool_calls=tool_calls)

    @staticmethod
    def tool_result(tool_call_id: str, name: str, content: str) -> "Message":
        return Message(
            role=Role.TOOL, content=content, tool_call_id=tool_call_id, name=name
        )
