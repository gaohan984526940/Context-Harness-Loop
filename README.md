<div align="center">

# 🧩 Context · Harness · Loop

### 一个最小、可运行、带教学注释的 AI Agent 脚手架

用 ~600 行 Python 讲清 Agent 开发的三层工程：**上下文 · 框架 · 循环**

<br>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Powered by DeepSeek](https://img.shields.io/badge/Powered%20by-DeepSeek-7c3aed.svg)](https://platform.deepseek.com/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/gaohan984526940/Context-Harness-Loop/pulls)

</div>

---

## ✨ 这个项目想回答三个问题

> **1. 三层工程到底是什么、区别在哪？**
> 三层显式映射到三个 Python 包，边界清晰、可独立替换。
>
> **2. Agent 为什么要「多步循环」，模型一次返回不行吗？**
> 用一个真实翻车实验说明：裸模型不会算数，会自信地编造。
>
> **3. 同一个模型，凭什么有的产品强有的弱？**
> 因为 Harness（工具 + 循环）才是能力上限的关键。

> 📖 完整教程见 **[`NOTES-三层工程对照.md`](./agent_scaffold/NOTES-三层工程对照.md)** —— 从"为什么需要循环"讲到每层在哪、怎么改，配真实代码行号。

---

## 🏗 三层结构

```
┌─────────────────────────────────────────────────────┐
│  loop/      最外 · 驱动 observe→think→act 迭代到完成   │  怎么转
│  ┌───────────────────────────────────────────────┐  │
│  │  harness/   中间 · 模型的手和嘴（工具/客户端/防护）│  │  周围搭什么
│  │  ┌─────────────────────────────────────────┐  │  │
│  │  │  context/   最内 · 每一步进入模型的 token  │  │  │  喂什么
│  │  │            [ DeepSeek 推理 ]              │  │  │
│  │  └─────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

| 包 | 工程层 | 职责 |
|----|--------|------|
| 🧠 `context/` | **Context Engineering** | 组装喂给模型的 token：消息结构、记忆裁剪、上下文拼装 |
| 🔧 `harness/` | **Harness Engineering** | 模型周围的支架：LLM 客户端、工具注册/分发、防护栏 |
| 🔁 `loop/` | **Loop Engineering** | 驱动迭代：agentic loop 本体、终止与错误恢复策略 |

---

## 🚀 快速开始

```bash
# 1. 克隆 & 装依赖
git clone https://github.com/gaohan984526940/Context-Harness-Loop.git
cd Context-Harness-Loop
pip install -r agent_scaffold/requirements.txt

# 2. 配置 DeepSeek key
cp agent_scaffold/.env.example agent_scaffold/.env
#    编辑 .env，填入你的 DEEPSEEK_API_KEY

# 3. 从仓库根目录运行
python -m agent_scaffold.main
```

启动后是一个 CLI 对话 Agent，终端会逐行打印 `THINK / ACT / OBSERVE`，让三层运转过程**肉眼可见**：

```text
你 > 先算 123×456，再加 789，再除以 3，最后判断奇偶
   [THINK  ] 第 1 步：组装上下文并请求模型…
   [ACT    ] 调用工具 calculator({'expression': '123 * 456'})
   [OBSERVE] calculator → 56088
   [THINK  ] 第 2 步：组装上下文并请求模型…
   [ACT    ] 调用工具 calculator({'expression': '56088 + 789'})
   [OBSERVE] calculator → 56877
   ...
助手 > 最终结果 18959，是奇数 ✅
```

### 试试这些输入

| 输入 | 看到什么 |
|------|---------|
| `你好，介绍下自己` | 不调工具，模型一步直接答 |
| `现在几点？` | 触发 `current_time` 工具，2 步循环 |
| `先算 123×456，再加 789，再除以 3，最后判断奇偶` | 连环计算，4 步循环 |

---

## 🤖 DeepSeek 模型说明

| 模型 | 工具调用 | 说明 |
|------|:-------:|------|
| `deepseek-chat` (V3) | ✅ | **默认，推荐** |
| `deepseek-reasoner` (R1) | ❌ | 推理强但无 function calling，切到它工具会失效 |

在 `.env` 用 `DEEPSEEK_MODEL` 切换。换成任何 OpenAI 兼容服务，只需改 `.env` 的 `DEEPSEEK_BASE_URL`。

---

## 🔌 怎么扩展

| 我想… | 改哪 |
|-------|------|
| 加一个新工具 | `agent_scaffold/harness/builtin_tools.py` 写带 `@tool` 的函数 |
| 换模型 / 厂商 | 改 `.env` 的 `BASE_URL` / `MODEL` |
| 改记忆 / 上下文策略 | `agent_scaffold/context/memory.py`（保持接口不变，上层不动） |
| 加安全拦截 | `agent_scaffold/harness/guardrails.py` |
| 调最大步数 / 错误容忍 | `.env` 的 `AGENT_MAX_STEPS`，或 `agent_scaffold/loop/policy.py` |

> 详见 [`NOTES-三层工程对照.md`](./agent_scaffold/NOTES-三层工程对照.md) 的「改动速查」。

---

## 🧭 三层归因法（调试 Agent 时最实用）

任务做砸了，先问自己是哪一层：

| 现象 | 层 | 去看 |
|------|-----|------|
| 模型**看错 / 没看到**该看的信息 | 🧠 Context | `context/memory.py`、system prompt |
| 模型**想对了但做不到**（工具缺失 / 越权 / 解析失败） | 🔧 Harness | `harness/tools.py`、`guardrails.py` |
| **单步都对但整体跑偏**（死循环 / 中途放弃 / 绕圈） | 🔁 Loop | `loop/agent.py`、`policy.py` |

---

## 📄 License

本项目采用 [MIT](./LICENSE) 许可证。

<div align="center">
<sub>如果这个项目帮你理解了 Agent 三层工程，欢迎 ⭐ Star 支持。</sub>
</div>
