"""入口 —— 装配三层并跑一个 CLI 对话 Agent。

运行（从【项目根目录】，即 agent_scaffold 的上一级）：
    python -m agent_scaffold.main

这个文件是"装配现场"：可以清楚看到 Context / Harness / Loop 三层
如何通过依赖注入拼成一个完整的 Agent。
"""

from __future__ import annotations

import sys

# Windows 终端默认 GBK，强制 stdin/stdout/stderr 用 UTF-8，避免读写中文/符号时编码崩溃。
# stdin 尤其关键：漏掉它会让中文输入被 GBK 解码成孤立代理字符，序列化请求体时抛 UnicodeEncodeError。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")

# 支持两种运行方式：包内 `python -m agent_scaffold.main` 或目录内 `python main.py`
try:
    from .config import Config
    from .context import ContextBuilder, Memory
    from .harness import Guardrails, LLMClient, ToolRegistry
    from .harness import builtin_tools  # noqa: F401 import 即注册内置工具
    from .loop import Agent, LoopPolicy
except ImportError:
    from config import Config
    from context import ContextBuilder, Memory
    from harness import Guardrails, LLMClient, ToolRegistry
    from harness import builtin_tools  # noqa: F401
    from loop import Agent, LoopPolicy


SYSTEM_PROMPT = """你是一个有用的 AI 助手，可以使用工具来完成任务。
当需要计算、查时间、读文件时，请调用相应的工具，不要自己编造结果。
回答简洁、准确。"""

# 可观测性：把三层运转的每个阶段打印出来，让 loop 过程肉眼可见。
# 用纯文本标签（不用 emoji），避免 Windows GBK 终端编码报错。
_COLORS = {
    "think": "THINK  ",
    "act": "ACT    ",
    "observe": "OBSERVE",
    "guard": "GUARD  ",
    "loop": "LOOP   ",
    "answer": "ANSWER ",
}


def _on_event(phase: str, msg: str) -> None:
    label = _COLORS.get(phase, phase)
    if phase == "answer":
        return  # 最终答案单独打印，避免重复
    print(f"   [{label}] {msg}")


def build_agent() -> Agent:
    """装配三层 —— 这就是脚手架的核心：用构造函数把三层注入到一起。"""
    config = Config.load()

    # ② Harness 层
    llm = LLMClient(config)
    tools = ToolRegistry()
    guardrails = Guardrails()

    # ① Context 层
    context_builder = ContextBuilder(system_prompt=SYSTEM_PROMPT)
    memory = Memory(max_messages=40)

    # ③ Loop 层
    policy = LoopPolicy(max_steps=config.max_steps)

    # 三层汇合
    return Agent(
        llm=llm,
        tools=tools,
        context_builder=context_builder,
        memory=memory,
        policy=policy,
        guardrails=guardrails,
        on_event=_on_event,
    )


def main() -> None:
    try:
        agent = build_agent()
    except RuntimeError as e:
        print(f"启动失败: {e}", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print("三层工程 Agent 脚手架（DeepSeek）。输入问题，输入 /quit 退出。")
    print(f"可用工具: {', '.join(agent_tool_names(agent))}")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n你 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见。")
            break

        if not user_input:
            continue
        if user_input in ("/quit", "/exit"):
            print("再见。")
            break

        answer = agent.run(user_input)
        print(f"\n助手 > {answer}")


def agent_tool_names(agent: Agent) -> list[str]:
    # 小helper：从 agent 里掏出工具名用于展示
    return agent._tools.names()  # noqa: SLF001 仅用于 CLI 展示


if __name__ == "__main__":
    main()
