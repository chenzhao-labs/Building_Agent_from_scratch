# Lesson 05 代码目录

## 目录说明

本目录包含 Lesson 05（Agentic RAG）的所有代码文件。课程演示如何构建一个能自主决定何时检索外部知识库的 AI Agent，以及迭代的 Producer-Checker 模式。

## 学习方法

每课遵循三步走：

1. **读概念** → 先读 `../README.md` 理解 Agentic RAG 的核心机制和迭代检索模式
2. **用原生 API 实现** → 不依赖 Agent 框架，仅用 `openai` SDK 手写 tool calling 循环，理解 Agent 如何在每轮自主决定是否检索
3. **用 qwen-agent 框架重写** → 用框架的 `Assistant`、`@register_tool` 等高层 API 重写，体会框架藏掉了什么

> 先裸写再看框架，两遍下来你既知道机制，也会用工具提效。

---

## 文件清单

| 文件 | 类型 | 框架 | 模型提供商 | 可运行 |
|------|------|------|-----------|--------|
| `05-python-agent-framework.py` | 学习代码 | 无框架，`openai` SDK | 通义千问 (DashScope) | **是** |
| `05-qwen-agent-framework.py` | 学习代码 | qwen-agent | 通义千问 (DashScope) | **是** |

### 文件详情

#### 05-python-agent-framework.py

**学习第一步：手写 tool calling 循环 + 知识库搜索。**

- 依赖：`pip install openai python-dotenv`
- 配置：环境变量 `DASHSCOPE_API_KEY`

核心内容：
- **知识库**：`TRAVEL_KNOWLEDGE_BASE` 硬编码 4 个目的地的信息
- **搜索工具**：`search_travel_knowledge(query)` — 接受查询参数，在知识库中匹配
- **基础 RAG Agent**：系统提示要求 Agent 在回答前始终先检索知识库
- **Producer-Checker Agent**：系统提示要求 Agent 检索 → 用目的地名再次检索获取完整详情 → 比较验证

和 Lesson 01 的关键区别：Lesson 01 的工具无参数（`get_destinations()`），本课的搜索工具接受 `query` 参数，Agent 需要自主决定"搜索什么关键词"。

#### 05-qwen-agent-framework.py

**学习第二步：用 qwen-agent 框架重写。**

- 依赖：`pip install -U "qwen-agent[gui]"`
- 配置：环境变量 `DASHSCOPE_API_KEY`

对比底层版，框架替你做了：
- **参数传递** — `BaseTool.parameters` 定义参数 schema，框架自动处理参数解析和传递
- **Tool calling 循环** — `Assistant.run()` 内部自动完成多轮检索
- **工具注册** — `@register_tool` 装饰器自动生成 Schema

## 本课核心概念

- **Agentic RAG**：Agent 自主决定何时检索、检索什么，而非固定的"先检索后生成"流程
- **Producer-Checker 模式**：第一轮检索获取初步信息 → 第二轮用更精确的关键词验证 → 比较后输出结论
- **工具作为数据源**：外部知识库被封装为 Agent 可调用的工具，检索只是 Agent 可执行的另一种操作
- **迭代检索**：Agent 可以在单次对话中多次调用搜索工具，每次用不同的查询参数

## 延伸

- 上一课：[04 工具使用](../../04-tool-use/README.md)
- 下一课：[06 构建可信赖 Agent](../../06-building-trustworthy-agents/README.md)
- 在生产环境中，可以将 `TRAVEL_KNOWLEDGE_BASE` 替换为真正的 Azure AI Search、向量数据库或知识图谱
