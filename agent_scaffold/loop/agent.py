"""Agent —— agentic loop 本体，三层工程在这里汇合。

一次 run() 就是一个完整的循环：
    observe(用户输入)
      → think(Context 组装 → Harness 调模型)
        → act(Harness 执行工具)
          → observe(工具结果回填)
            → think → ... 直到模型不再调工具 或 触发 LoopPolicy 终止。

本层只负责"编排节律"，具体能力都委托给注入的三层组件——
依赖注入让每一层都能独立替换、独立测试。
"""

from __future__ import annotations

from collections.abc import Callable

from ..context import ContextBuilder, Memory, Message
from ..harness import Guardrails, LLMClient, ToolRegistry
from .policy import LoopPolicy


class Agent:
    """把 Context / Harness / Loop 三层装配成一个可对话的 Agent。"""

    def __init__(
        self,
        llm: LLMClient,
        tools: ToolRegistry,
        context_builder: ContextBuilder,
        memory: Memory,
        policy: LoopPolicy,
        guardrails: Guardrails | None = None,
        on_event: Callable[[str, str], None] | None = None,
    ) -> None:
        self._llm = llm
        self._tools = tools
        self._ctx = context_builder
        self._memory = memory
        self._policy = policy
        self._guardrails = guardrails or Guardrails()
        # on_event(阶段, 内容)：可观测性钩子，让三层运转过程肉眼可见
        self._emit = on_event or (lambda phase, msg: None)

    def run(self, user_input: str) -> str:
        """处理一轮用户输入，跑完整个 agentic loop，返回最终回答。"""
        # === OBSERVE：把用户输入纳入记忆 ===
        self._memory.append(Message.user(user_input))

        consecutive_errors = 0
        step = 0
        tools_schema = self._tools.openai_schema()

        while True:
            # 终止条件①：超过最大步数
            if self._policy.should_stop(step):
                self._emit("loop", f"已达最大步数 {self._policy.max_steps}，停止。")
                return "（已达最大迭代步数，任务未完成）"
            step += 1

            # === THINK：Context 层组装上下文 → Harness 层调模型 ===
            self._emit("think", f"第 {step} 步：组装上下文并请求模型…")
            messages = self._ctx.build_messages(self._memory)
            response = self._llm.chat(messages, tools=tools_schema)

            # 模型不再调工具 → 给出最终答案，循环结束
            if not response.wants_tools:
                answer = response.content or ""
                self._memory.append(Message.assistant(answer))
                self._emit("answer", answer)
                return answer

            # 模型决定调工具：先把这条 assistant(含 tool_calls) 存入记忆
            self._memory.append(
                Message.assistant(response.content, tool_calls=response.tool_calls)
            )

            # === ACT：Harness 层解析并执行工具 ===
            calls = self._tools.parse(response.tool_calls)
            step_had_error = False
            for call in calls:
                self._emit("act", f"调用工具 {call.name}({call.arguments})")

                # 防护栏检查
                allowed, reason = self._guardrails.check(call)
                if not allowed:
                    self._emit("guard", reason)
                    self._memory.append(
                        Message.tool_result(call.id, call.name, reason)
                    )
                    step_had_error = True
                    continue

                result = self._tools.execute(call)
                self._emit("observe", f"{call.name} → {result.content}")
                # === OBSERVE：工具结果回填记忆，进入下一轮 ===
                self._memory.append(
                    Message.tool_result(result.tool_call_id, result.name, result.content)
                )
                if not result.ok:
                    step_had_error = True

            # 错误恢复策略：连续多步出错则中止
            consecutive_errors = consecutive_errors + 1 if step_had_error else 0
            if self._policy.should_abort_on_errors(consecutive_errors):
                self._emit("loop", "连续工具错误过多，中止。")
                return "（工具连续出错，任务中止）"
