"""工具系统 —— Harness 的核心。

用装饰器 @tool 注册函数；ToolRegistry 负责：
  1. 生成 OpenAI 兼容的 tools schema（给模型看）
  2. 解析模型发来的 tool_calls，分发执行，返回结果（给模型回填）

加一个新工具 = 写一个带 @tool 的函数，框架代码不动。
"""

from __future__ import annotations

import inspect
import json
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ToolCall:
    """模型请求的一次工具调用（已解析）。"""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    """工具执行结果。回填给模型时对应一条 role=tool 的消息。"""

    tool_call_id: str
    name: str
    content: str
    ok: bool = True


# Python 基础类型 → JSON Schema 类型 的简单映射
_PY_TO_JSON = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


@dataclass(frozen=True)
class _ToolSpec:
    name: str
    description: str
    func: Callable[..., Any]
    schema: dict[str, Any]


def _build_schema(func: Callable[..., Any]) -> dict[str, Any]:
    """从函数签名 + 类型注解 + docstring 自动生成 JSON Schema。"""
    sig = inspect.signature(func)
    properties: dict[str, Any] = {}
    required: list[str] = []

    for pname, param in sig.parameters.items():
        annotation = param.annotation if param.annotation is not inspect.Parameter.empty else str
        json_type = _PY_TO_JSON.get(annotation, "string")
        properties[pname] = {"type": json_type}
        if param.default is inspect.Parameter.empty:
            required.append(pname)

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


# 全局收集装饰器注册的工具，再由 ToolRegistry 收编。
_PENDING: list[_ToolSpec] = []


def tool(func: Callable[..., Any]) -> Callable[..., Any]:
    """把一个函数注册为工具。description 取自函数的 docstring。"""
    spec = _ToolSpec(
        name=func.__name__,
        description=(inspect.getdoc(func) or "").strip() or func.__name__,
        func=func,
        schema=_build_schema(func),
    )
    _PENDING.append(spec)
    return func


class ToolRegistry:
    """工具注册表：持有全部工具，负责 schema 导出与执行分发。"""

    def __init__(self) -> None:
        self._tools: dict[str, _ToolSpec] = {}
        # 收编所有用 @tool 装饰、已 import 的函数
        for spec in _PENDING:
            self._tools[spec.name] = spec

    def openai_schema(self) -> list[dict[str, Any]]:
        """导出给模型的 tools 定义。"""
        return [
            {
                "type": "function",
                "function": {
                    "name": s.name,
                    "description": s.description,
                    "parameters": s.schema,
                },
            }
            for s in self._tools.values()
        ]

    def parse(self, raw_tool_calls: tuple[dict[str, Any], ...]) -> list[ToolCall]:
        """把 LLM 原始 tool_calls 解析成结构化 ToolCall。"""
        calls: list[ToolCall] = []
        for tc in raw_tool_calls:
            fn = tc["function"]
            try:
                args = json.loads(fn["arguments"]) if fn["arguments"] else {}
            except json.JSONDecodeError:
                args = {}
            calls.append(ToolCall(id=tc["id"], name=fn["name"], arguments=args))
        return calls

    def execute(self, call: ToolCall) -> ToolResult:
        """执行单个工具调用。任何异常都转成 ok=False 的结果回填，绝不让循环崩。"""
        spec = self._tools.get(call.name)
        if spec is None:
            return ToolResult(
                tool_call_id=call.id,
                name=call.name,
                content=f"错误：未知工具 '{call.name}'",
                ok=False,
            )
        try:
            result = spec.func(**call.arguments)
            return ToolResult(
                tool_call_id=call.id,
                name=call.name,
                content=str(result),
                ok=True,
            )
        except Exception as e:  # noqa: BLE001 工具失败不应中断 agent loop
            return ToolResult(
                tool_call_id=call.id,
                name=call.name,
                content=f"工具执行出错: {e}",
                ok=False,
            )

    def names(self) -> list[str]:
        return list(self._tools.keys())
