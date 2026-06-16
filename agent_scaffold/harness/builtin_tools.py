"""开箱即用的内置工具。

仅作演示——展示"加工具只需写函数"。import 本模块即完成注册。
真实项目把你自己的工具按同样的方式写在这里或独立模块即可。
"""

from __future__ import annotations

import ast
import operator
from datetime import datetime

from .tools import tool

# 安全的四则运算：用 AST 解析，绝不用 eval。
_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("仅支持数字")
    if isinstance(node, ast.BinOp):
        return _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp):
        return _OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("不支持的表达式")


@tool
def calculator(expression: str) -> str:
    """计算一个数学表达式，支持 + - * / ** %。例如 "3 * (4 + 5)"。"""
    tree = ast.parse(expression, mode="eval")
    return str(_safe_eval(tree.body))


@tool
def current_time() -> str:
    """返回当前的日期和时间。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def read_file(path: str) -> str:
    """读取指定路径的文本文件内容（最多返回前 4000 字符）。"""
    import os

    if not os.path.isfile(path):
        return f"错误：文件不存在或不是普通文件：{path}"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read(4000)
    except UnicodeDecodeError:
        return f"错误：文件不是 UTF-8 文本，无法读取：{path}"
