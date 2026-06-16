"""Context Engineering 层 —— 决定每一步喂给模型的 token。

职责边界：
  - 只负责【组装上下文】，不负责调用模型，也不负责循环。
  - message.py  消息的不可变数据结构
  - memory.py   历史的存储、裁剪、压缩
  - builder.py  把 system + memory + tools 拼成发给 LLM 的最终 payload
"""

from .message import Message, Role
from .memory import Memory
from .builder import ContextBuilder

__all__ = ["Message", "Role", "Memory", "ContextBuilder"]
