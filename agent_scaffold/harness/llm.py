"""LLM 客户端 —— 模型抽象层。

封装 OpenAI 兼容接口。对上层(loop)只暴露一个 chat() 方法和一个干净的
LLMResponse 结构，把"对接哪家模型"的细节锁在这一层。
换模型 = 换这层，上层不动。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from openai import OpenAI

from ..config import Config


@dataclass(frozen=True)
class LLMResponse:
    """一次模型返回的归一化结果。

    content    模型的自然语言输出（可能为 None，当它只想调工具时）
    tool_calls 模型请求的工具调用列表（OpenAI 原始结构，原样保留以便回填）
    finish     结束原因：stop / tool_calls / length 等
    """

    content: str | None
    tool_calls: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    finish: str = "stop"

    @property
    def wants_tools(self) -> bool:
        return len(self.tool_calls) > 0


class LLMClient:
    """对接 DeepSeek（OpenAI 兼容）的薄封装。"""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.request_timeout,
        )

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """发起一次对话补全。

        tools 为空时不传 tools 参数（兼容 deepseek-reasoner 等不支持工具的模型）。
        """
        kwargs: dict[str, Any] = {
            "model": self._config.model,
            "messages": messages,
            "temperature": self._config.temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        try:
            resp = self._client.chat.completions.create(**kwargs)
        except Exception as e:  # 边界处统一包装，给上层清晰错误
            raise RuntimeError(f"LLM 请求失败: {e}") from e

        choice = resp.choices[0]
        msg = choice.message

        # 把 SDK 对象归一化成我们自己的不可变结构
        tool_calls: tuple[dict[str, Any], ...] = ()
        if msg.tool_calls:
            tool_calls = tuple(
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            )

        return LLMResponse(
            content=msg.content,
            tool_calls=tool_calls,
            finish=choice.finish_reason or "stop",
        )
