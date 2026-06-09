# Lesson 03 代码目录

## 目录说明

本目录包含 Lesson 03（Agentic 设计模式）的所有代码文件。课程以"旅行目的地推荐"为场景，展示三种构建高效 AI Agent 的基础设计模式。

## 学习方法

三步走：

1. **读概念** → 先读 `../README.md`，理解三种设计模式要解决的问题
2. **用原生 API 实现** → 手写 tool calling 循环 + Pydantic 解析 + 多 agent 协作
3. **用 qwen-agent 框架重写** → 用 `Assistant` 感受框架的便利

---

## 文件清单

| 文件 | 类型 | 框架 | 模型提供商 | 可运行 |
|------|------|------|-----------|--------|
| `03-python-agent-framework.py` | 学习代码 | 无框架，`openai` SDK | 通义千问 (DashScope) | **是** |
| `03-qwen-agent-framework.py` | 学习代码 | qwen-agent | 通义千问 (DashScope) | **是** |

### 三种模式说明

#### 模式 1：清晰的 Agent 指令

最有效也最简单的模式。好的指令定义三件事：

- **角色（我是谁）** — "你是一位名叫 Alex 的奢华旅行礼宾专员"
- **职责（我该做什么）** — 分步骤的明确职责列表
- **约束（我该怎么做）** — 语气、格式、边界

#### 模式 2：结构化输出

自由文本适合对话，但下游代码需要结构化数据。通过：

1. 用 **Pydantic** 定义输出 schema（`DestinationRecommendation`、`TravelRecommendations`）
2. 在 system_message 中指定 **JSON 格式要求**
3. LLM 输出 JSON 后，用 `model_validate_json()` 验证和解析

#### 模式 3：单一职责 Agent

软件工程的"关注点分离"原则应用到 Agent 设计：

- **DestinationExpert** — 只管目的地研究和推荐（配 `get_destination_details` 工具）
- **LogisticsPlanner** — 只管行程规划（无工具，纯推理）

两个 Agent 顺序协作：DestinationExpert 产出推荐 → LogisticsPlanner 基于推荐做规划。

---

## 核心对比

| 概念 | 原生 SDK | qwen-agent |
|------|----------|------------|
| 清晰指令 | `SYSTEM_PROMPT` 常量 | `Assistant(system_message=...)` |
| 结构化输出 | Pydantic 模型 + `model_validate_json()` | 同上，无框架级支持 |
| 单一职责 | 不同的 `SYSTEM_PROMPT` + 函数编排 | 不同的 `Assistant` 实例 + `run_agent()` 编排 |
| 工具定义 | `TOOLS_SCHEMA` + `TOOL_MAP` | `@register_tool` + `BaseTool` |
| tool calling 循环 | `while True` 手动循环 | `Assistant.run()` 内部自动处理 |

---

## 环境准备

### 1. 获取 API Key

[阿里云百炼平台](https://bailian.console.aliyun.com/) → 开通 DashScope → 获取 API Key。

### 2. 配置环境变量

```bash
# 项目根目录 .env
DASHSCOPE_API_KEY=sk-你的APIKey
```

### 3. 安装依赖

```bash
# 底层版
pip install openai python-dotenv pydantic

# qwen-agent 版
pip install -U "qwen-agent[gui]" pydantic
```

### 4. 运行

```bash
cd 03-agentic-design-patterns/code_samples

python 03-python-agent-framework.py   # 先手写
python 03-qwen-agent-framework.py     # 再看框架
```

---

## 延伸

- 上一课：[02 探索 Agent 框架](../../02-explore-agentic-frameworks/code_samples/README.md)
- 下一课：[04 工具使用](../../04-tool-use/README.md)
- 千问 API 文档：[DashScope OpenAI 兼容接口](https://help.aliyun.com/zh/model-studio/qwen-api-reference-hk)
- qwen-agent 源码：[QwenLM/Qwen-Agent](https://github.com/QwenLM/Qwen-Agent)
