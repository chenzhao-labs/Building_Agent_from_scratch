# Lesson 07 代码目录

## 目录说明

本目录包含 Lesson 07（规划设计模式）的所有代码文件。课程演示如何将复杂旅行请求拆分为结构化子任务（Planning Agent），然后由 Concierge Agent 按依赖顺序执行。

## 学习方法

每课遵循三步走：

1. **读概念** → 先读 `../README.md` 理解规划设计模式的核心：任务分解 → 结构化输出 → 分派执行
2. **用原生 API 实现** → 不依赖 Agent 框架，仅用 `openai` SDK + Pydantic 手写规划-执行分离的全流程
3. **用 qwen-agent 框架重写** → 用框架的 `Assistant`、`@register_tool` 重写，对比两层的接口差异

> 本课是三批课程中代码量最大的（300行/230行），涉及 Pydantic 模型、JSON response_format、多工具 tool calling，是综合实战。

---

## 文件清单

| 文件 | 类型 | 框架 | 模型提供商 | 可运行 |
|------|------|------|-----------|--------|
| `07-python-agent-framework.py` | 学习代码 | 无框架，`openai` SDK | 通义千问 (DashScope) | **是** |
| `07-qwen-agent-framework.py` | 学习代码 | qwen-agent | 通义千问 (DashScope) | **是** |

### 文件详情

#### 07-python-agent-framework.py

**学习第一步：手写规划-执行全流程。**

- 依赖：`pip install openai python-dotenv pydantic`
- 配置：环境变量 `DASHSCOPE_API_KEY`

核心架构（两层分离）：

**规划层 — `create_travel_plan()`**
- 使用 `response_format={"type": "json_object"}` 让 LLM 输出结构化 JSON
- Pydantic 模型 `TravelPlan` / `TravelSubTask` 做输出校验
- LLM 根据用户请求自动分解为航班、酒店、活动等子任务，设定优先级和依赖关系

**执行层 — `run_concierge()`**
- 手动 tool calling 循环，处理 3 个工具：`book_flight`、`reserve_hotel`、`book_activity`
- Concierge Agent 按依赖顺序遍历子任务，调用对应工具
- 每个工具返回模拟的确认号

关键对比：Lesson 01/04 只有一个 Agent 做工具调用，本课的 Agent 先生成任务计划、再执行——"想清楚再动手"。

#### 07-qwen-agent-framework.py

**学习第二步：用 qwen-agent 框架重写。**

- 依赖：`pip install -U "qwen-agent[gui]" pydantic`
- 配置：环境变量 `DASHSCOPE_API_KEY`

对比底层版：
- 3 个工具分别定义为 `BookFlight`、`ReserveHotel`、`BookActivity` 类（继承 `BaseTool`）
- 规划 Agent 使用 `Assistant(function_list=[])` 纯文本对话
- 执行 Agent 使用 `Assistant(function_list=["book_flight", "reserve_hotel", "book_activity"])` 工具调用
- JSON 解析增加了 ` ```json ``` ` 包裹的容错处理

| 原始 MAF | 原生 SDK | qwen-agent |
|----------|---------|------------|
| `response_format=TravelPlan`（Pydantic 自动绑定） | `response_format={"type": "json_object"}` + 手动 `model_validate_json()` | 同左，加 markdown 容错 |
| `@tool` 装饰函数 | 手写 `TOOLS_SCHEMA` + `TOOL_MAP` | `@register_tool` + `BaseTool` 类 |

## 本课核心概念

- **任务分解**：将"7天巴黎旅行"拆分为航班、酒店、活动等独立子任务
- **结构化输出**：Pydantic 模型保证下游代码拿到的是已验证的数据结构，而非自由文本
- **规划-执行分离**：Planning Agent 决定"做什么"，Concierge Agent 执行"怎么做"
- **依赖管理**：子任务间有先后依赖（先订机票再订酒店），Agent 需按序执行
- **优先级**：high/medium/low 三级，在预算紧张时可跳过低优先级任务

## 延伸

- 上一课：[06 构建可信赖 Agent](../../06-building-trustworthy-agents/README.md)
- 下一课：[08 多 Agent](../../08-multi-agent/README.md)
- 进阶：可以用 `response_format` 的 `json_schema` 模式（需模型支持）替代 `json_object`，实现更严格的 schema 约束
