# Lesson 08 代码目录

## 目录说明

本目录包含 Lesson 08（多Agent设计模式）的所有代码文件。课程覆盖多Agent编排的**三种核心模式**：流水线式、并发式、条件式。

原始课程在 `workflows-agent-framework/` 子目录下有 4 个 notebook（basic / sequential / concurrent / condition），使用 MAF 的 `WorkflowBuilder` 构建。本目录的迁移用 LangGraph 和 qwen-agent 实现了相同的三种模式。

## 学习方法

三步走：

1. **读概念** → 先读 `../README.md`，理解多Agent的适用场景和构建模块
2. **用 LangGraph 实现** → 学习 `StateGraph` / `Send` / `conditional_edges` 三种编排原语
3. **用 qwen-agent 手动编排** → 理解在没有编排框架时如何手动实现同样的模式

---

## 文件清单

| 文件 | 类型 | 编排方式 | 模型提供商 | 可运行 |
|------|------|---------|-----------|--------|
| `08-python-agent-framework.py` | 学习代码 | LangGraph (`StateGraph` + `Send` + `conditional_edges`) | 通义千问 (DashScope) | **是** |
| `08-qwen-agent-framework.py` | 学习代码 | qwen-agent `Assistant` + 手动/asyncio 编排 | 通义千问 (DashScope) | **是** |

### 三个模式说明

#### 模式 1：流水线式 (Sequential)

`Sales-Agent` → `Price-Agent` → `Quote-Agent`。家具采购三阶段管道，每个 Agent 的输出是下一个的输入。

- **LangGraph 版**：`add_edge("sales", "price")` → `add_edge("price", "quote")` → `compile()`
- **qwen-agent 版**：`run_agent(sales) → run_agent(price, sales_output) → run_agent(quote, price_output)`

#### 模式 2：并发式 (Concurrent / Fan-out)

`Dispatcher` → (`Researcher` ‖ `Planner`) → `Aggregate`。研究目的地和制定行程并行执行，结果汇总展示。

- **LangGraph 版**：`add_conditional_edges` + `Send` API 实现 fan-out 到多个节点，`Annotated[list, operator.add]` reducer 收集并行结果
- **qwen-agent 版**：`asyncio.gather(run_agent_async(researcher), run_agent_async(planner))` 并行执行两个 Assistant

#### 模式 3：条件式 (Conditional)

`Writer` → `Reviewer` → (`PASS` → `Publisher` / `REVISE` → 回到 `Writer` 重写)。内容审核流水线，根据审核结果动态选择下游路径，最多重写 3 轮。

- **LangGraph 版**：`add_conditional_edges("reviewer", route_after_review, {...})` 根据 state 中的 `review_result` 路由
- **qwen-agent 版**：解析 Reviewer 回复的首行（`PASS` / `REVISE`），`if/else` 决定下一步

---

## 核心对比

| 编排模式 | LangGraph | qwen-agent |
|---------|-----------|------------|
| **流水线** | `add_edge` 链，节点间自动传递 state | 手动 `run_agent(a1) → f"上一步输出:\n{output}" → run_agent(a2)` |
| **并发** | `Send` API + `add_conditional_edges` fan-out，`operator.add` reducer 收集结果 | `asyncio.gather()` 并行执行多个 Assistant |
| **条件** | `add_conditional_edges` + 路由函数，原生支持循环 | `if/else` 解析中间输出 + `for` 循环重试 |
| **可视化** | `graph.get_graph().draw_mermaid()` | 无（代码结构即编排逻辑） |
| **状态管理** | `TypedDict` + `Annotated` reducer 自动合并 | 手动变量传递 |
| **依赖** | `openai` + `langgraph` | `qwen-agent[gui]` |

### 三种模式的适用场景

| 模式 | 适用场景 | 特征 |
|------|---------|------|
| 流水线 | 文档处理、内容审核、ETL | 步骤有严格先后顺序，下游依赖上游 |
| 并发 | 多角度分析、批量处理、研究汇总 | 任务互不依赖，可同时进行，最后汇总 |
| 条件 | 审核-发布、质量门控、分级路由 | 中间结果决定后续路径，可能有循环 |

---

## 环境准备

```bash
# LangGraph 版
pip install openai langgraph python-dotenv

# qwen-agent 版
pip install -U "qwen-agent[gui]" python-dotenv
```

### 运行

```bash
cd 08-multi-agent/code_samples

python 08-python-agent-framework.py
python 08-qwen-agent-framework.py
```

---

## 延伸

- 上一课：[07 规划设计](../../07-planning-design/code_samples/README.md)
- 下一课：[09 元认知](../../09-metacognition)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [qwen-agent 源码](https://github.com/QwenLM/Qwen-Agent)
