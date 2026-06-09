# 探索 AI Agent 框架

AI Agent 框架是简化 Agent 创建、部署和管理的软件平台。它们提供预构建组件、抽象和工具，让开发者专注于业务逻辑，而不是底层基础设施。

## 介绍

本课将涵盖：

- 什么是 AI Agent 框架，它们解决了什么问题？
- Agent 框架的四层抽象：Client → Agent → Tools → Session
- 为什么先手写再学框架是最有效的学习路径

## 学习目标

- 理解 Agent 框架在 AI 开发中的角色
- 掌握 Client / Agent / Tools / Session 四层抽象的本质
- 能用手写代码映射到框架 API，不被框架"黑盒"困住

## 什么是 AI Agent 框架

AI Agent 框架提供了构建智能 Agent 的标准化基础设施。无论哪个框架（LangChain、AutoGen、qwen-agent 等），底层都在做同一件事：

```
把 LLM + 工具 + 消息管理 打包在一起，让你用几行代码就能创建能自主调度工具的 Agent。
```

### 框架替你做了三件事

1. **Tool Schema 自动生成** — 你用装饰器/类定义工具，框架自动生成 JSON Schema 交给 LLM
2. **Tool Calling 循环** — `while True` 循环由框架内部维护，你不需要手写
3. **消息/会话管理** — 多轮对话的消息列表由框架自动追加和追踪

## Agent 框架的四层抽象

本项目使用的 qwen-agent 框架，四层抽象映射如下：

| 层级 | 职责 | qwen-agent 实现 | 原生 SDK 对应 |
|------|------|----------------|--------------|
| **Client** | 连接 AI 模型 | `llm_cfg = {"model_type": "qwen_dashscope"}` | `OpenAI(base_url="https://dashscope...")` |
| **Agent** | 封装 Client + 指令 + 工具 | `Assistant(llm=..., system_message=..., function_list=[...])` | 手动维护 messages + system prompt |
| **Tools** | 让 LLM 能"做事"的函数 | `@register_tool("name")` + `BaseTool` | JSON Schema 字典 + Python 函数 |
| **Session** | 多轮对话记忆 | messages 列表手动维护 | messages 列表手动维护 |

### 以代码为例

原生 SDK 版（手写四层）：

```python
# Client
client = OpenAI(api_key=..., base_url="https://dashscope.aliyuncs.com/...")

# Tools
TOOLS_SCHEMA = [{"type": "function", "function": {...}}]
TOOL_MAP = {"check_destination_availability": check_destination_availability}

# Agent
SYSTEM_PROMPT = "你是一个旅行预订代理..."

# Session
session = [{"role": "system", "content": SYSTEM_PROMPT}]

# 运行（手写 tool calling 循环）
while True:
    response = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS_SCHEMA)
    msg = response.choices[0].message
    if not msg.tool_calls:
        return msg.content
    for tc in msg.tool_calls:
        result = TOOL_MAP[tc.function.name](**args)
        messages.append({"role": "tool", "content": result})
```

qwen-agent 框架版（框架帮你做了循环）：

```python
# Client
llm_cfg = {"model": "qwen-flash", "model_type": "qwen_dashscope", "api_key": api_key}

# Tools
@register_tool("check_destination_availability")
class CheckDestinationAvailability(BaseTool):
    description = "检查度假目的地是否可预订。"
    parameters = [{"name": "destination", "type": "string", "description": "...", "required": True}]
    def call(self, params, **kwargs): ...

# Agent（Client + Tools + Instructions 打包在一起）
agent = Assistant(
    llm=llm_cfg,
    name="TravelAvailabilityAgent",
    system_message="你是一个旅行预订代理...",
    function_list=["check_destination_availability"],
)

# 运行（框架内部完成 tool calling 循环）
for responses in agent.run(messages=[{"role": "user", "content": "..."}]):
    print(responses[-1]["content"])
```

## 为什么先手写再学框架

直接学框架会遇到"黑盒困惑"：

- `agent.run()` 为什么能自动调用工具？
- 多轮对话的记忆存在哪里？
- 如果工具调用失败，Agent 怎么处理？

手写一遍四层抽象后，这些问题自然消失。你会理解：

- Agent 的本质 = LLM + 工具 + 循环控制流
- 框架只是把你能手写的代码封装了一层
- 换任何框架都只是换语法糖，底层机制不变

> **先理解，再用工具。而不是反过来。**

## 代码示例

- 原生 SDK 版：[02-python-agent-framework.py](./code_samples/02-python-agent-framework.py)
- qwen-agent 框架版：[02-qwen-agent-framework.py](./code_samples/02-qwen-agent-framework.py)
- 代码学习指南：[code_samples/README.md](./code_samples/README.md)

## 延伸阅读

- [qwen-agent 源码](https://github.com/QwenLM/Qwen-Agent)
- [DashScope OpenAI 兼容接口](https://help.aliyun.com/zh/model-studio/qwen-api-reference-hk)

## 上一课

[AI Agent 及其用例简介](../01-intro-to-ai-agents/README.md)

## 下一课

[理解 Agentic 设计模式](../03-agentic-design-patterns/README.md)
