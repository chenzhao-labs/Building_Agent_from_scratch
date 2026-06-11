<div align="center">

<img src="https://img.shields.io/badge/Phase-1%20Complete-brightgreen?style=for-the-badge" />
<img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" />
<img src="https://img.shields.io/badge/Model-Qwen%20Flash-orange?style=for-the-badge" />
<img src="https://img.shields.io/badge/API-DashScope-ff69b4?style=for-the-badge" />
<img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" />

</div>

<br/>

# 🧱 Building Agent from Scratch

> *从零开始构建 AI Agent —— 用最少的依赖，理解最深的原理。*

<br/>

## 🤔 Why：为什么要做这个项目

微软的 [**AI Agents for Beginners**](https://github.com/microsoft/ai-agents-for-beginners) 是一份优秀的入门课程，但它有两个门槛：

<p align="center">
  <img src="https://img.shields.io/badge/❌-Azure%20账号必需-red?style=flat-square" />
  <img src="https://img.shields.io/badge/❌-框架内部机制不可见-red?style=flat-square" />
  <img src="https://img.shields.io/badge/❌-代码不可直接运行-red?style=flat-square" />
</p>

| 痛点 | 说明 |
|------|------|
| 🔐 **Azure 门槛** | 所有代码基于 Microsoft Agent Framework + Azure AI Foundry，需要 Azure 订阅和已部署的模型 |
| 📦 **框架黑盒** | `provider.create_agent()` 一行代码背后隐藏了 tool calling 循环、消息管理、结构化输出等核心机制 |
| 🚫 **不可运行** | 课程代码是 `.ipynb` 参考代码，需要 Azure 环境，无法本地直接跑 |

### 这个项目解决什么

<div align="center">

| 🎯 | | |
|:---:|---|---|
| **零门槛** | → | 只用一个 DashScope API Key，所有代码 `python xxx.py` 直接跑通 |
| **裸写优先** | → | 每课两版代码：先手写底层循环，再用框架重写 |
| **框架迁移力** | → | 穿透 API 看到本质——所有 Agent 框架底层都一样 |

</div>

> ⚡ **这不是微软课程的"翻译"，而是一次"解剖"** —— 把框架拆开，看清楚每一层在做什么。

<br/>

## 📦 What：项目是什么

一个 **AI Agent 从零到一的学习路径**，以"旅行代理"为贯穿场景，覆盖 Agent 开发全部分核心概念。

### 核心特色

```
┌───────────────────────────────────────────────────────────┐
│                                                           │
│   📖 读概念    →    ✍️ 手写原生版    →    🚀 用框架重写    │
│   (README)         (XX-python-agent-     (XX-qwen-agent-  │
│                     framework.py)         framework.py)   │
│                                                           │
│   理解要解决        看清框架的            体会框架替你       │
│   什么问题          "内脏"              做了什么            │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

<div align="center">

| 特色 | |
|------|-----|
| 🔬 **双版本学习** | 每节课 = 原生 SDK 版（手写所有机制）+ qwen-agent 框架版 |
| 🇨🇳 **国内友好** | 模型用 DashScope（通义千问），Agent 框架用 qwen-agent |
| ▶️ **即装即用** | 每个 `.py` 文件都可以直接 `python xxx.py` 运行 |
| 🧱 **逐层递进** | tool calling → 多工具 → 多 Agent → RAG → 记忆 → 生产 |

</div>

### 两版代码对比

```python
# ── 原生版：30 行看清 Agent 的底层机制 ──
while True:
    response = client.chat.completions.create(
        model="qwen-flash", messages=messages, tools=TOOLS_SCHEMA
    )
    msg = response.choices[0].message
    if not msg.tool_calls:
        return msg.content        # LLM 给出最终回答，循环结束
    # 执行工具 → 结果写回 → 继续循环
    for tc in msg.tool_calls:
        result = TOOL_MAP[tc.function.name](**args)
        messages.append({"role": "tool", "content": result})

# ── 框架版：5 行，框架替你封装了上面的循环 ──
agent = Assistant(llm=llm_cfg, system_message="...",
                  function_list=["get_destinations"])
for responses in agent.run(messages):
    print(responses[-1]["content"])
```

### 框架迁移对照

| 微软原版 (MAF) | 本项目 | 
|:---|:---|
| `AzureAIProjectAgentProvider` | `OpenAI(base_url="https://dashscope.aliyuncs.com/...")` |
| `@tool(approval_mode="...")` | `@register_tool("name")` + `BaseTool` |
| `provider.create_agent()` | `Assistant(llm=..., function_list=[...])` |
| `WorkflowBuilder` | Python 函数顺序调用 / `Assistant` 链式传递 |
| `agent.create_session()` | `messages = []` 手动维护多轮历史 |
| GPT-4o / GPT-4o-mini | Qwen-Flash / Qwen-Plus |

<br/>

## 🛠️ How：怎么做

### 三步学习循环

```
            ┌────────────┐
            │  📖 读概念 │
            │  README    │
            └─────┬──────┘
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
┌───────────────┐   ┌───────────────┐
│ ✍️ 原生版     │   │ 🚀 框架版     │
│ 手写底层机制   │   │ 体会抽象便利   │
│               │   │               │
│ tool calling  │   │ Assistant     │
│ while True    │   │ @register_tool│
│ JSON Schema   │   │ agent.run()   │
└───────────────┘   └───────────────┘
```

**第一遍（原生版）** 你看到的是 Agent 框架的"内脏"：`while True` 循环、JSON Schema、messages 列表充当日志记忆

**第二遍（框架版）** 你体会到框架替你做了什么：自动 Schema 生成、tool calling 循环、消息管理

### 快速开始

```bash
# 1️⃣  获取 API Key（免费额度）
# 👉 阿里云百炼平台：https://bailian.console.aliyun.com/

# 2️⃣  配置
echo 'DASHSCOPE_API_KEY=sk-你的APIKey' > .env

# 3️⃣  安装
pip install openai python-dotenv pydantic        # 原生版依赖
pip install -U "qwen-agent[gui,rag,code_interpreter,mcp]"                 # 框架版依赖

# 4️⃣  跑起来
cd 01-intro-to-ai-agents/code_samples
python 01-python-agent-framework.py   # 先手写，理解底层
python 01-qwen-agent-framework.py     # 再看框架，体会封装
```

<br/>

## 🗺️ 内容导航

### 🟢 第一阶段：打好基础

| # | 课程 | 你会学到 | 
|:---:|------|------|
| 01 | [AI 代理介绍](./01-intro-to-ai-agents/code_samples/README.md) | Agent 定义、tool calling 循环、tool schema |
| 02 | [探索 Agent 框架](./02-explore-agentic-frameworks/code_samples/README.md) | Client → Agent → Tools → Session 四层抽象 |
| 03 | [Agentic 设计模式](./03-agentic-design-patterns/code_samples/README.md) | 清晰指令、结构化输出(Pydantic)、单一职责 |
| 04 | [工具使用](./04-tool-use/code_samples/README.md) | 多工具组合、工具审批模式 |

### 🟢 第二阶段：进阶模式

| # | 课程 | 你会学到 |
|:---:|------|------|
| 05 | Agentic RAG | 检索增强生成、Maker-Checker 模式 |
| 06 | 构建可信赖 Agent | 系统提示设计、安全约束 |
| 07 | 规划设计 | 任务分解、子任务编排 |

### ⚪ 第三阶段：多 Agent 系统

| # | 课程 | 你会学到 |
|:---:|------|------|
| 08 | 多 Agent 系统 | 顺序工作流、Agent 管线 |
| 09 | 元认知 | 自我反思、回退策略、自我评估 |
| 11 | Agentic 协议 | MCP 模式、Agent 间通信 |

### ⚪ 第四阶段：工程化

| # | 课程 | 你会学到 |
|:---:|------|------|
| 10 | AI Agent 生产化 | 可观测性、评估、成本管理 |
| 12 | 上下文工程 | 上下文窗口管理、摘要工具 |
| 13 | Agent 记忆 | 工作/短期/长期记忆 |

### ⚪ 独立模块

| # | 课程 | 你会学到 |
|:---:|------|------|
| 15 | 浏览器使用 | Playwright、浏览器自动化 |
| 18 | AI Agent 安全 | 签名收据、可信执行 |

<br/>

## 📁 项目结构

```
Building_Agent_from_scratch/
│
├── 📄 README.md                              ← 你在这里
│
├── 📗 01-intro-to-ai-agents/                 ← AI 代理介绍
│   ├── README.md
│   └── code_samples/
│       ├── README.md
│       ├── 01-python-agent-framework.py        ✅ 原生版
│       └── 01-qwen-agent-framework.py          ✅ 框架版
│
├── 📗 02-explore-agentic-frameworks/         ← 探索 Agent 框架
│   ├── README.md
│   └── code_samples/
│       ├── 02-python-agent-framework.py        ✅
│       └── 02-qwen-agent-framework.py          ✅
│
├── 📗 03-agentic-design-patterns/            ← Agentic 设计模式
│   ├── README.md
│   └── code_samples/
│       ├── 03-python-agent-framework.py        ✅
│       └── 03-qwen-agent-framework.py          ✅
│
├── 📗 04-tool-use/                           ← 工具使用
│   ├── README.md
│   └── code_samples/
│       ├── 04-python-agent-framework.py        ✅
│       └── 04-qwen-agent-framework.py          ✅
│
├── 📘 05-agentic-rag/                        ← agentic rag使用
│   ├── README.md
│   └── code_samples/
│       ├── 04-python-agent-framework.py        ✅
│       └── 04-qwen-agent-framework.py          ✅
├── 📘 06-building-trustworthy-agents/        ← [待完成]
├── 📘 07-planning-design/                    ← [待完成]
├── 📘 08-multi-agent/                        ← [待完成]
├── 📘 09-metacognition/                      ← [待完成]
├── 📘 10-ai-agents-production/               ← [待完成]
├── 📘 11-agentic-protocols/                  ← [待完成]
├── 📘 12-context-engineering/                ← [待完成]
├── 📘 13-agent-memory/                       ← [待完成]
├── 📕 14-microsoft-agent-framework/          ← [跳过]
├── 📘 15-browser-use/                        ← [待完成]
└── 📘 18-securing-ai-agents/                 ← [待完成]
```

<br/>

## 🔗 相关资源

| 资源 | 链接 |
|------|------|
| 📖 原课程 | [microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) |
| 🔑 API Key | [阿里云百炼 DashScope](https://bailian.console.aliyun.com/) |
| 🧩 qwen-agent | [QwenLM/Qwen-Agent](https://github.com/QwenLM/Qwen-Agent) |
| 📄 API 文档 | [DashScope OpenAI 兼容接口](https://help.aliyun.com/zh/model-studio/qwen-api-reference-hk) |

<br/>

<div align="center">

## 📄 License

本项目基于 [微软 AI Agents for Beginners](https://github.com/microsoft/ai-agents-for-beginners) 改编 · MIT License

</div>
