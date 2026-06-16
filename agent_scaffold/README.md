# 三层工程 Agent 脚手架

一个**最小但完整、可运行**的 Agent 框架，把 AI Agent 开发的三层工程显式映射到三个 Python 包，每层边界清晰、可独立替换。基于 **DeepSeek**（OpenAI 兼容接口）。

```
┌─────────────────────────────────────────────┐
│            loop/   Loop Engineering           │  ← 怎么转：迭代、终止、错误恢复
│  ┌─────────────────────────────────────────┐ │
│  │      harness/  Harness Engineering      │ │  ← 周围搭什么：工具、客户端、防护
│  │   ┌───────────────────────────────────┐ │ │
│  │   │   context/  Context Engineering   │ │ │  ← 喂什么：每一步的输入 token
│  │   │        [ DeepSeek 推理 ]          │ │ │
│  │   └───────────────────────────────────┘ │ │
│  └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

## 目录结构与三层对应

| 包 | 工程层 | 职责 | 关键文件 |
|----|--------|------|----------|
| `context/` | **Context Engineering** | 组装喂给模型的 token | `message.py` 不可变消息 · `memory.py` 历史裁剪 · `builder.py` 上下文组装 |
| `harness/` | **Harness Engineering** | 模型周围的支架 | `llm.py` 模型客户端 · `tools.py` 工具注册/分发 · `builtin_tools.py` 内置工具 · `guardrails.py` 防护栏 |
| `loop/` | **Loop Engineering** | 驱动迭代 | `agent.py` agentic loop · `policy.py` 终止/恢复策略 |
| `main.py` | 装配现场 | 用依赖注入把三层拼起来 | — |

> 📖 **想深入理解？** 读 [`NOTES-三层工程对照.md`](./NOTES-三层工程对照.md)：
> 从"为什么需要循环"（含裸模型翻车实验）讲到每层在哪、怎么改，配真实代码行号。

## 快速开始

```bash
# 1. 装依赖
pip install -r agent_scaffold/requirements.txt

# 2. 配置 DeepSeek key
cp agent_scaffold/.env.example agent_scaffold/.env
# 编辑 .env，填入 DEEPSEEK_API_KEY

# 3. 从【项目根目录】（agent_scaffold 的上一级）运行
python -m agent_scaffold.main
```

> 注意用 `-m` 模块方式从根目录启动，而不是 `cd` 进去跑 `python main.py`——
> 因为框架内部使用了包相对导入。

运行后是一个 CLI 对话 Agent，终端会打印每一步的 `THINK / ACT / OBSERVE`，让三层运转过程肉眼可见。试试：

- `123 * 456 等于多少？` → 触发 calculator 工具
- `现在几点？` → 触发 current_time 工具

## DeepSeek 模型说明（重要）

| 模型 | 工具调用 | 适用 |
|------|---------|------|
| `deepseek-chat` (V3) | ✅ 支持 | **本框架默认，推荐** |
| `deepseek-reasoner` (R1) | ❌ 不支持 | 纯推理对话；切到它后工具会失效 |

在 `.env` 里通过 `DEEPSEEK_MODEL` 切换。

## 如何替换每一层

三层通过**构造函数注入**（见 `main.py` 的 `build_agent()`），每层都能独立替换：

- **换模型**：只改 `harness/llm.py`，上层不动。换成任何 OpenAI 兼容服务只需改 `.env` 的 `BASE_URL`/`MODEL`。
- **加工具**：在 `builtin_tools.py`（或新模块）里写个带 `@tool` 的函数即可，框架代码不动。
- **改记忆策略**：把 `context/memory.py` 的滑动窗口换成摘要压缩 / 向量召回（RAG），接口不变。
- **改循环行为**：调 `loop/policy.py` 的终止与错误恢复参数。

## 三层归因法（调试 Agent 时）

任务做砸了怎么定位？

- 模型**看错了信息** → **Context** 问题
- 模型**想对了但做不到**（工具缺失/越权/解析失败） → **Harness** 问题
- 模型**单步都对但整体跑偏**（该停不停/绕圈） → **Loop** 问题
