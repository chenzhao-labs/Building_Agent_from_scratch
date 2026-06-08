# Lesson 01 代码目录

## 目录说明

本目录包含 Lesson 01（AI Agents介绍）的所有代码文件。课程以"旅行Agents"为场景，演示如何构建一个能够调用工具、查询目的地信息的 AI Agent。

## 学习方法

每课遵循三步走：

1. **读概念** → 先读 `../README.md` 理解本课要解决的问题和核心机制
2. **用原生 API 实现** → 不依赖 Agent 框架，仅用 `openai` SDK + 模型 API 手写 tool calling 循环，理解底层发生了什么
3. **用 qwen-agent 框架重写** → 用框架的 `Assistant`、`@register_tool` 等高层 API 重写，体会框架藏掉了什么、提供了什么

> 先裸写再看框架，两遍下来你既知道机制，也会用工具提效。

---

## 文件清单

| 文件 | 类型 | 框架 | 模型提供商 | 可运行 |
|------|------|------|-----------|--------|
| `01-python-agent-framework.py` | 学习代码 | 无框架，`openai` SDK | 通义千问 (DashScope) | **是** |
| `01-qwen-agent-framework.py` | 学习代码 | qwen-agent | 通义千问 (DashScope) | **是** |

### 文件详情

#### 01-python-agent-framework.py

**学习第一步：手写 tool calling 循环。**

- 依赖：`pip install openai python-dotenv`
- 配置：环境变量 `DASHSCOPE_API_KEY`

核心代码是 `run_agent()` 中的 `while True` 循环：

```python
while True:
    response = client.chat.completions.create(messages, tools)
    if not msg.tool_calls:
        return msg.content  # 结束
    # 执行工具 → 追加结果 → 继续循环
```

这个 30 行的循环就是所有 Agent 框架的底层本质。理解了这个，MAF、LangChain、qwen-agent 对你来说就是各种语法糖。

关键概念：
- **Tool Schema** — 告诉 LLM 你有什么工具、每个工具有什么参数（JSON Schema 格式）
- **Tool Calling 循环** — LLM 输出 tool_calls → 你执行函数 → 结果写回 messages → 再次调用 LLM
- **流式输出** — 先完成 tool calling（非流式），最终文本回复用流式输出

#### 01-qwen-agent-framework.py

**学习第二步：用 qwen-agent 框架重写。**

- 依赖：`pip install -U "qwen-agent[gui]"`
- 配置：环境变量 `DASHSCOPE_API_KEY`

对比底层版，框架替你做了：
- **Tool calling 循环** — `Assistant.run()` 内部自动处理
- **消息管理** — 多轮对话历史自动维护
- **工具注册** — `@register_tool` 装饰器自动生成 Schema
- **流式输出** — 生成器模式天然支持增量产出

| 原版 MAF | qwen-agent |
|----------|------------|
| `@tool(approval_mode="never_require")` | `@register_tool("name")` |
| `AzureAIProjectAgentProvider(credential=...)` | `llm_cfg = {"model_type": "qwen_dashscope"}` |
| `provider.create_agent(tools=[...], instructions=...)` | `Assistant(llm=llm_cfg, function_list=[...], system_message=...)` |
| `await agent.run("...")` | `for responses in agent.run(messages=[...])` |

---

## 环境准备

### 1. 获取 API Key

在[阿里云百炼平台](https://bailian.console.aliyun.com/) 开通 DashScope 服务，获取 API Key（格式 `sk-xxx`）。

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
cd translations/zh-CN/01-intro-to-ai-agents/code_samples

# 先跑底层版，理解 tool calling 循环
python 01-python-agent-framework.py

# 再跑框架版，对比接口差异
python 01-qwen-agent-framework.py
```

---

## 本课核心概念

- **AI Agent** = LLM + 工具 + 环境。不是单一模型，而是一个系统。
- **Tool Calling** = Agent 框架的核心机制。LLM 决定"何时调用哪个工具，传什么参数"，代码负责执行。
- **Agent 类型**：简单反射型、基于目标型、学习型、多 Agent 系统等（详见课程 README）。

## 延伸

- 下一课：[02 探索 Agent 框架](../../02-explore-agentic-frameworks/README.md)
- 千问 API 文档：[DashScope OpenAI 兼容接口](https://help.aliyun.com/zh/model-studio/qwen-api-reference-hk)
- qwen-agent 源码：[QwenLM/Qwen-Agent](https://github.com/QwenLM/Qwen-Agent)
