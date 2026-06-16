"""防护栏 —— 在工具执行前拦截危险调用。

Harness 的"安全带"。这里给一个最小实现：基于工具名 + 参数的简单黑名单/确认钩子。
真实项目可扩展为：权限系统、人工审批、路径白名单、速率限制等。
"""

from __future__ import annotations

from collections.abc import Callable

from .tools import ToolCall


class Guardrails:
    """工具调用前的校验。返回 (允许?, 拒绝原因)。"""

    def __init__(self, confirm: Callable[[ToolCall], bool] | None = None) -> None:
        # confirm: 可选的人工确认回调。返回 False 则拒绝执行。
        self._confirm = confirm

    def check(self, call: ToolCall) -> tuple[bool, str]:
        """对单个工具调用做安全检查。"""
        # 示例规则：读文件时禁止越权访问敏感路径
        if call.name == "read_file":
            path = str(call.arguments.get("path", ""))
            blocked = (".env", "id_rsa", "shadow", ".ssh")
            if any(b in path for b in blocked):
                return False, f"已被防护栏拦截：禁止读取敏感文件 '{path}'"

        # 可选人工确认
        if self._confirm is not None and not self._confirm(call):
            return False, "用户拒绝了该工具调用"

        return True, ""
