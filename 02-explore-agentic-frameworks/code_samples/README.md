# Lesson 02 代码目录

## 目录说明

本目录包含 Lesson 02（探索 Agent 框架）的所有代码文件。课程以"旅行预订代理"为场景，展示 Agent 框架的四层抽象：**Client → Agent → Tools → Session**。

## 学习方法

每课遵循三步走：

1. **读概念** → 先读 `../README.md` 理解 Agent 框架的四层架构
2. **用原生 API 实现** → 不依赖 Agent 框架，仅用 `openai` SDK + 模型 API 手写四层抽象，理解框架底层在做什么
3. **用 qwen-agent 框架重写** → 用框架的 `Assistant`、`@register_tool` 等高层 API 重写，体会框架藏掉了什么

> 先裸写再看框架，两遍下来你既知道机制，也会用工具提效。

---

## 文件清单

| 文件 | 类型 | 框架 | 模型提供商 | 可运行 |
|------|------|------|-----------|--------|
| `02-python-agent-framework.py` | 学习代码 | 无框架，`openai` SDK | 通义千问 (DashScope) | **是** |
| `02-qwen-agent-framework.py` | 学习代码 | qwen-agent | 通义千问 (DashScope) | **是** |

### 文件详情

#### 02-python-agent-framework.py

**学习第一步：手写 Agent 框架四层抽象。**

- 依赖：`pip install openai python-dotenv`
- 配置：环境变量 `DASHSCOPE_API_KEY`

代码中明确定义了四层结构：

```python
# 第一层：Client — 与 AI 模型的连接
client = OpenAI(api_key=..., base_url="https://dashscope.aliyuncs.com/...")

# 第二层：Tools — 工具定义（JSON Schema + Python 函数）
TOOLS_SCHEMA = [{...}]
TOOL_MAP = {"check_destination_availability": check_destination_availability}

# 第三层：Agent — Client + Instructions + Tools 的封装
SYSTEM_PROMPT = "你是一个旅行预订代理..."

# 第四层：Session — messages 列表的多轮记忆
session = [{"role": "system", "content": SYSTEM_PROMPT}]
run_agent("第1轮", session)  # session 保持引用，agent 记得历史
run_agent("第2轮", session)
```

关键概念：
- **Tool Schema** — JSON Schema 格式的工具描述，告诉 LLM 你有什么工具
- **Tool Calling 循环** — LLM 输出 tool_calls → 执行函数 → 结果写回 → 再次调用 LLM
- **Session（多轮记忆）** — 同一个 messages 列表在多次 `run_agent()` 调用间共享

#### 02-qwen-agent-framework.py

**学习第二步：用 qwen-agent 框架重写。**

- 依赖：`pip install -U "qwen-agent[gui]"`
- 配置：环境变量 `DASHSCOPE_API_KEY`

对比底层版，框架替你做了：
- **Tool Schema 生成** — `BaseTool` 类的 `parameters` 列表自动转为 JSON Schema
- **Tool Calling 循环** — `Assistant.run()` 内部自动循环
- **消息管理** — agent 返回完整的 messages 列表，外部保持即可实现多轮对话

| 原版 MAF | qwen-agent |
|----------|------------|
| `AzureAIProjectAgentProvider(credential=...)` | `llm_cfg = {"model_type": "qwen_dashscope"}` |
| `@tool(approval_mode="never_require")` | `@register_tool("name")` + `BaseTool` |
| `provider.create_agent(name=..., instructions=..., tools=...)` | `Assistant(llm=llm_cfg, name=..., system_message=..., function_list=[...])` |
| `session = agent.create_session()` | `session = []` （手动维护 messages 列表） |
| `await agent.run("...", session=session)` | `run_turn("...", session)` （生成器模式迭代 `agent.run()`） |

---

## 环境准备

### 1. 获取 API Key

在[阿里云百炼平台](https://bailian.console.aliyun.com/) 开通 DashScope 服务，获取 API Key。

### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

```
DASHSCOPE_API_KEY=sk-你的APIKey
```

### 3. 安装依赖

```bash
# 底层版所需
pip install openai python-dotenv

# qwen-agent 版所需
pip install -U "qwen-agent[gui]"
```

### 4. 运行

```bash
cd 02-explore-agentic-frameworks/code_samples

# 先跑底层版，理解四层抽象
python 02-python-agent-framework.py

# 再跑框架版，对比接口差异
python 02-qwen-agent-framework.py
```

---

## 本课核心概念

- **Client** — 连接 AI 模型的桥梁。原生 SDK 里是 `OpenAI(base_url=...)`，框架里是 `llm_cfg`。
- **Agent** — 把 Client + 指令 + 工具打包在一起的东西。这是你直接交互的对象。
- **Tools** — 让 LLM 能"做事"的函数。Tool Schema 告诉 LLM 有什么、传什么参数。
- **Session** — 多轮对话的记忆。本质上就是一个 messages 列表在多次调用间保持引用。
- **Tool Calling 循环** — LLM 说"我要调这个工具" → 你执行 → 结果写回 → LLM 再决策。这是所有 Agent 框架的核心机制。

## 延伸

- 上一课：[01 AI 代理介绍](../../01-intro-to-ai-agents/code_samples/README.md)
- 下一课：[03 Agentic 设计模式](../../03-agentic-design-patterns/code_samples/README.md)
- 千问 API 文档：[DashScope OpenAI 兼容接口](https://help.aliyun.com/zh/model-studio/qwen-api-reference-hk)
- qwen-agent 源码：[QwenLM/Qwen-Agent](https://github.com/QwenLM/Qwen-Agent)
