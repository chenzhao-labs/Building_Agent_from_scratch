# Lesson 04 代码目录

## 目录说明

本目录包含 Lesson 04（工具使用设计模式）的所有代码文件。课程以"旅行预订代理"为场景，展示如何定义、组合和安全管理多个工具。

## 学习方法

三步走：

1. **读概念** → 先读 `../README.md`，理解 Tool Calling 的设计模式
2. **用原生 API 实现** → 手写多工具 Schema + tool calling 循环 + 审批拦截
3. **用 qwen-agent 框架重写** → 用 `@register_tool` + `Assistant` 感受框架的便利

---

## 文件清单

| 文件 | 类型 | 框架 | 模型提供商 | 可运行 |
|------|------|------|-----------|--------|
| `04-python-agent-framework.py` | 学习代码 | 无框架，`openai` SDK | 通义千问 (DashScope) | **是** |
| `04-qwen-agent-framework.py` | 学习代码 | qwen-agent | 通义千问 (DashScope) | **是** |

### 三个示例说明

#### 示例 1：多工具组合

Agent 同时持有 `get_destinations`、`check_availability`、`get_flight_info` 三个工具。LLM 自主决定调用顺序和参数。核心机制：把多个工具的 JSON Schema 一起传给 LLM，LLM 根据用户意图选择最合适的工具。

#### 示例 2：结构化输出

通过 Pydantic 模型（`BookingRecommendation`、`TravelPlan`）定义输出格式，system_message 中指定 JSON 输出约束，最后用 `model_validate_json()` 解析。下游代码拿到的是验证过的类型安全对象，而不是需要正则解析的自由文本。

#### 示例 3：工具审批模式

`book_flight` 是有副作用的敏感操作。在工具执行前通过 `input()` 拦截，需要人工输入 `y` 确认才真正执行。MAF 用 `approval_mode="always_require"` 参数实现，qwen-agent 和原生 SDK 都在工具函数内部实现相同的拦截逻辑。

---

## 核心对比

| 概念 | 原生 SDK | qwen-agent |
|------|----------|------------|
| 工具定义 | `TOOLS_SCHEMA` (JSON Schema) + Python 函数 | `@register_tool` + `BaseTool` 子类 |
| 多工具组合 | 全部放入 `TOOLS_SCHEMA` 列表传给 LLM | `function_list=["tool1", "tool2", ...]` |
| 工具参数 | `parameters.properties` + `required` | `parameters` 列表，每个参数含 `name`/`type`/`required` |
| 结构化输出 | system_message 指定 JSON + Pydantic 验证 | 同左，qwen-agent 无框架级 `response_format` |
| 审批模式 | 在 tool calling 循环中拦截 SENSITIVE_TOOLS | 在 `BaseTool.call()` 内部用 `input()` 拦截 |
| tool calling 循环 | `while True` 手动管理 | `Assistant.run()` 内部自动完成 |

---

## 环境准备

```bash
# 底层版
pip install openai python-dotenv pydantic

# qwen-agent 版
pip install -U "qwen-agent[gui]" pydantic
```

### 运行

```bash
cd 04-tool-use/code_samples

python 04-python-agent-framework.py
python 04-qwen-agent-framework.py

# 要体验工具审批模式，编辑代码取消注释 demo_3_approval_mode()
```

---

## 延伸

- 上一课：[03 Agentic 设计模式](../../03-agentic-design-patterns/code_samples/README.md)
- 下一课：[05 Agentic RAG](../../05-agentic-rag/README.md)
- [千问 API 文档](https://help.aliyun.com/zh/model-studio/qwen-api-reference-hk)
- [qwen-agent 源码](https://github.com/QwenLM/Qwen-Agent)
