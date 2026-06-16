"""短期记忆 —— 对话历史的存储与裁剪。

Context Engineering 的核心痛点之一：上下文窗口有限，历史会无限增长。
这里用最朴素但有效的策略——保留 system + 最近 N 轮，超出则裁掉最旧的非 system 消息。

生产环境可在此替换为：摘要压缩(compaction)、向量召回(RAG)、分层记忆等。
接口保持不变，上层(builder/loop)无需改动。
"""

from __future__ import annotations

from .message import Message, Role


class Memory:
    """历史消息容器。对外只暴露 append / snapshot / 裁剪，不暴露可变列表。"""

    def __init__(self, max_messages: int = 40) -> None:
        # max_messages：非 system 消息的保留上限。超出触发裁剪。
        self._max_messages = max_messages
        self._messages: list[Message] = []

    def append(self, message: Message) -> None:
        """追加一条消息，并按策略裁剪。"""
        self._messages.append(message)
        self._truncate()

    def extend(self, messages: list[Message]) -> None:
        for m in messages:
            self.append(m)

    def snapshot(self) -> tuple[Message, ...]:
        """返回当前历史的不可变快照。Context 层据此组装。"""
        return tuple(self._messages)

    def _truncate(self) -> None:
        """裁剪策略：system 消息永远保留，其余只留最近 max_messages 条。

        这是"上下文压缩"最简单的形态：滑动窗口。
        """
        system_msgs = [m for m in self._messages if m.role == Role.SYSTEM]
        other_msgs = [m for m in self._messages if m.role != Role.SYSTEM]

        if len(other_msgs) > self._max_messages:
            other_msgs = other_msgs[-self._max_messages:]

        self._messages = system_msgs + other_msgs

    def __len__(self) -> int:
        return len(self._messages)
