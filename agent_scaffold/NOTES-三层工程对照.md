# 三层工程对照笔记

> 结合本脚手架代码，逐层讲清 **每层在哪、负责什么、怎么改**。
> 所有行号对应仓库当前代码，可直接定位。

## 为什么需要循环（先回答最根本的疑问）

> "模型一次返回不就行了，为啥要分多步？"

因为**大模型本质是文字接龙——它会"预测下一个词"，但不会真正计算、也不掌握实时信息**。在它不擅长的地方，它会自信地编造。多走一步循环去调工具，就是用可靠的事实替换不可靠的猜测。

**真实实验**（同一道题 `987654321 ÷ 12345`，标准答案 `80004.40024…`）：

| 方式 | 模型给的答案 | 对不对 |
|------|-------------|--------|
| 不给工具，让模型硬算 | `80006.99927` | ❌ 整数位就错了（差 2），小数全是编造 |
| 给工具，走 Agent 循环 | `80004.40024` | ✅ 正确 |

硬算翻车的可怕之处：它错得**很像真的**，不核对根本看不出来（这就是 hallucination）。而 Agent 循环里，模型做的是它真正擅长的事——理解需求、决定调哪个工具、把结果整理成人话；精确计算外包给 `calculator`。

```
[THINK]   模型决定：大数除法我算不准 → 调工具
[ACT]     calculator(987654321 / 12345)
[OBSERVE] → 80004.40024301337          ← 真实计算，不是猜的
[THINK]   拿到可靠结果 → 格式化输出 → 结束
```

**一句话：** 一次返回，靠的是模型"已经知道"的东西；多步循环，是去获取/验证它"不知道或算不准"的东西。多出的那一步 `ACT→OBSERVE`，买的就是正确性——这正是 Agent 比纯聊天模型强的根本。

> 另一类必须循环的场景：**信息依赖**。如"查下现在几点，下午算 A、上午算 B"——模型必须先拿到 `current_time` 的结果才知道下一步分支，无法预先合并成一步。

### 常见误区：「可网页版 DeepSeek 算这题就对啊？」

会问这个，是把两个不同的东西做了对比：

| 你对比的 | 它到底是什么 |
|----------|-------------|
| 上面的翻车实验 | **裸模型 + 还被捆住手脚**（system prompt 明令"不许打草稿、不许分步、直接报数"），专门暴露模型本体不会算数 |
| 网页版 DeepSeek | **一个完整产品** = 模型 + Harness + 工具 + 思维链，是整体能力 |

网页版能算对，通常是这三种机制之一在起作用，**没有一种是靠"模型脑算"**：

1. **后台真的挂了代码执行工具**（写段 Python 跑一下）——和我们的 `calculator` 同理，只是工具更强；
2. **允许它打草稿（思维链 CoT）**——一步步列竖式，每步都是简单运算，比"一口报答案"准得多。而我的实验恰恰用 prompt **禁掉了**打草稿；
3. **system prompt 引导它"遇到精确计算就用工具、别硬算"**——和我们 Agent 里"模型决定调 calculator"是同一个决策。

**一句话点破：** 你在网页版看到的正确答案，不是裸模型的能力，而是 **DeepSeek 这个产品（模型 + Harness）整体的能力**。这反过来正好证明了本脚手架的价值——

> **同一个底层模型，套不套 Harness（工具 + 循环），能力上限天差地别。网页版强，不是模型多神，而是它把 Harness 做好了。你搭的脚手架，做的是同一件事。**

可亲手验证：在网页版**关掉"深度思考"**并要求"不许打草稿、直接报数"，再问那道大数除法 → 大概率翻车；正常问 → 它列过程/调工具 → 答对。

---

## 总览：一句话定位

> **Context 管"喂什么 token"，Harness 管"周围搭什么"，Loop 管"怎么转起来"。**

它们不是平行的三件事，而是三个**抽象层**，由外向内包裹：

```
loop/      ← 最外：驱动 observe→think→act 迭代到完成
  harness/ ← 中间：模型的手和嘴（工具、客户端、防护）
    context/ ← 最内：每一步进入模型的 token
      [ DeepSeek 推理 ]
```

装配点在 `main.py:build_agent()`（约 60-83 行）——三层通过构造函数注入拼成一个 `Agent`。

---

## 一次提问，三层如何协同

以 `123 乘以 456 等于几？` 为例，对照 `loop/agent.py` 的 `run()`：

| 阶段 | 代码位置 | 哪一层在工作 |
|------|----------|-------------|
| 用户输入存入记忆 | `agent.py:48` | **Context**（Memory.append） |
| 组装上下文 | `agent.py:63` | **Context**（ContextBuilder） |
| 请求模型 | `agent.py:64` | **Harness**（LLMClient.chat） |
| 模型要调工具？ | `agent.py:67` | **Loop**（终止判断） |
| 解析工具调用 | `agent.py:79` | **Harness**（ToolRegistry.parse） |
| 防护栏检查 | `agent.py:85` | **Harness**（Guardrails） |
| 执行工具 | `agent.py:94` | **Harness**（ToolRegistry.execute） |
| 结果回填记忆 | `agent.py:97` | **Context**（Memory.append） |
| 错误恢复判断 | `agent.py:104-107` | **Loop**（LoopPolicy） |

> 关键洞察：`agent.py` 自己**几乎不实现任何能力**，它只负责"编排节律"，把具体工作委托给注入的三层组件。这就是分层的价值——改一层不动其它层。

---

## ① Context Engineering —— `context/`

**职责：决定每一步进入模型 context window 的 token。只组装，不调用模型、不管循环。**

| 文件 | 作用 | 关键锚点 |
|------|------|----------|
| `message.py` | 不可变消息结构 | `Message`（frozen dataclass）`message.py:26`；`to_openai()` 转协议 `message.py:46` |
| `memory.py` | 历史存储与裁剪 | `Memory.append()` `memory.py:25`；裁剪策略 `_truncate()` `memory.py:37` |
| `builder.py` | 上下文组装出口 | `build_messages()` `builder.py:18` |

### 怎么改

**改记忆策略（最常见）** —— 当前是滑动窗口（`memory.py:37` 只留最近 N 条非 system 消息）。要换成更强的策略：

- **摘要压缩（compaction）**：在 `_truncate()` 里，把要裁掉的旧消息先丢给一个小模型摘要，把摘要作为一条 system/assistant 消息塞回去。
- **向量召回（RAG）**：给 `Memory` 加一个向量库，`snapshot()` 时按当前 query 相关性召回历史片段，而非简单取最近 N 条。

**关键：只要保持 `append()` / `snapshot()` 两个方法的签名不变，`builder.py` 和 `agent.py` 完全不用动。** 这是分层的回报。

**改 system prompt** —— 在 `main.py:35` 的 `SYSTEM_PROMPT`。它由 `builder.py:23` 注入、不进 memory，所以永远在最前、不会被裁剪误伤。

**调试归因**：如果模型"看错了信息"（看到无关内容 / 没看到关键文档）→ 问题在这一层。

---

## ② Harness Engineering —— `harness/`

**职责：模型周围的支架。模型只会"token→token"，要让它真正做事，靠这一层提供手（工具）、嘴（客户端）、安全带（防护）。**

| 文件 | 作用 | 关键锚点 |
|------|------|----------|
| `llm.py` | 模型客户端（OpenAI 兼容） | `LLMClient.chat()` `llm.py:50`；归一化结果 `LLMResponse` `llm.py:18` |
| `tools.py` | 工具注册 + schema 生成 + 分发 | `@tool` 装饰器 `tools.py:80`；`execute()` `tools.py:122`；`openai_schema()` `tools.py:101` |
| `builtin_tools.py` | 开箱即用工具 | `calculator` / `current_time` / `read_file` |
| `guardrails.py` | 危险操作拦截 | `Guardrails.check()` `guardrails.py:18` |

### 怎么改

**加一个工具（最常见）** —— 在 `builtin_tools.py` 写个带 `@tool` 的函数即可，**框架代码一行不改**：

```python
@tool
def web_search(query: str) -> str:
    """联网搜索关键词，返回前几条结果摘要。"""
    ...  # 你的实现
    return result
```

原理：`@tool`（`tools.py:80`）自动从函数签名+类型注解生成 JSON Schema（`tools.py:67` 的 `_build_schema`），从 docstring 取 description。模型据此知道有这个工具、怎么调。`import builtin_tools` 时即完成注册（`main.py:30`）。

> 注意：工具的参数类型注解要写（`def f(x: str)`），否则默认当 string。docstring 要写清楚，那是模型决定是否调用的唯一依据。

**换模型 / 换厂商** —— 只动 `llm.py`。换任何 OpenAI 兼容服务（通义、Kimi、本地 vLLM、one-api 网关）只需改 `.env` 的 `DEEPSEEK_BASE_URL` 和 `DEEPSEEK_MODEL`。换非兼容协议（如 Anthropic 原生）才需要改 `chat()` 内部（`llm.py:50`），但只要 `chat()` 仍返回 `LLMResponse`，上层不动。

**加防护规则** —— 在 `guardrails.py:18` 的 `check()` 里加判断。当前已有示例：拦截读取 `.env`/`id_rsa` 等敏感文件（`guardrails.py:23`）。可扩展为路径白名单、权限校验、人工审批（构造时传 `confirm` 回调，`guardrails.py:15`）、速率限制。

**调试归因**：如果模型"想对了但做不到"（工具缺失、参数解析失败、越权被拦）→ 问题在这一层。注意 `execute()`（`tools.py:122`）把工具异常吞成 `ok=False` 的结果回填，**绝不让循环崩**——这是有意设计。

---

## ③ Loop Engineering —— `loop/`

**职责：驱动 Agent 一轮一轮转，并决定何时停、出错怎么办。**

| 文件 | 作用 | 关键锚点 |
|------|------|----------|
| `policy.py` | 终止与恢复策略 | `should_stop()` `policy.py:18`；`should_abort_on_errors()` `policy.py:22` |
| `agent.py` | agentic loop 本体 | `run()` 主循环 `agent.py:45`；`while True` `agent.py:54` |

### 循环的骨架（agent.py:54-107）

```
while True:
    if 超过最大步数: 停                      # agent.py:56  终止条件①
    组装上下文 → 调模型                       # agent.py:63-64
    if 模型不再调工具: return 答案            # agent.py:67  终止条件②（正常结束）
    解析工具 → 防护检查 → 执行 → 回填结果      # agent.py:79-101
    if 连续错误过多: 中止                      # agent.py:105 终止条件③（异常退出）
```

三个出口：达上限、正常完成、连续失败。**没有第四种走法**——这是防死循环的关键。

### 怎么改

**调终止行为** —— 改 `policy.py` 或构造参数。`max_steps`（防死循环硬上限）在 `main.py:71` 通过 `config.max_steps` 注入，可在 `.env` 改 `AGENT_MAX_STEPS`。`max_consecutive_errors`（`policy.py:14`）控制连续失败几次放弃。

**加反思（reflection）** —— 在每轮 `THINK` 前（`agent.py:62` 之前）插一步：让模型先评估"上一步做得对吗、要不要换策略"，把反思结果作为一条消息加进 memory。

**加子 agent / 并行** —— 当前是单循环串行执行工具（`agent.py:81` 的 for）。要并行：把循环体内的工具执行改成并发；要子 agent：在某个工具内部再 new 一个 `Agent` 跑子任务，只把结论回传（这正是"上下文隔离"——子 agent 的噪音不污染主循环的 context）。

**调试归因**：如果模型"单步都对但整体跑偏"（该停不停、错了不回头、绕圈子）→ 问题在这一层。

---

## 三层归因法（调 Agent 时最实用的一张表）

任务做砸了，先问自己是哪一层：

| 现象 | 层 | 去看 |
|------|-----|------|
| 模型看错/没看到该看的信息 | **Context** | `context/memory.py`、`SYSTEM_PROMPT` |
| 模型想对了但做不到（工具缺失/越权/解析失败） | **Harness** | `harness/tools.py`、`guardrails.py`、`llm.py` |
| 单步都对但整体跑偏（死循环/中途放弃/绕圈） | **Loop** | `loop/agent.py`、`policy.py` |

---

## 改动速查

| 我想… | 改哪 |
|-------|------|
| 加一个新工具 | `harness/builtin_tools.py` 写 `@tool` 函数 |
| 换模型/厂商 | `.env` 改 `BASE_URL`/`MODEL`；非兼容协议改 `harness/llm.py` |
| 改记忆/上下文策略 | `context/memory.py`（保持 append/snapshot 签名） |
| 改 system prompt | `main.py` 的 `SYSTEM_PROMPT` |
| 加安全拦截 | `harness/guardrails.py` 的 `check()` |
| 调最大步数/错误容忍 | `.env` 的 `AGENT_MAX_STEPS`，或 `loop/policy.py` |
| 改循环节律（反思/并行/子agent） | `loop/agent.py` 的 `run()` |
