# Lesson 06 代码目录

## 目录说明

本目录包含 Lesson 06（构建可信赖的 AI Agent）的所有代码文件。课程演示"系统消息框架"——用 meta-prompt 让 LLM 自动生成高质量的系统提示词。

## 学习方法

每课遵循三步走：

1. **读概念** → 先读 `../README.md` 理解系统消息框架的两步生成流程和安全设计原则
2. **用原生 API 实现** → 不依赖 Agent 框架，仅用 `openai` SDK 实现 meta-prompt → 生成 system prompt → 验证的三步流程
3. **用 qwen-agent 框架重写** → 用框架的 `Assistant` 重写，对比无工具场景下的接口差异

> 本课无工具调用，重点在于理解"如何用 LLM 生成更好的 LLM 指令"这一元层次设计。

---

## 文件清单

| 文件 | 类型 | 框架 | 模型提供商 | 可运行 |
|------|------|------|-----------|--------|
| `06-python-agent-framework.py` | 学习代码 | 无框架，`openai` SDK | 通义千问 (DashScope) | **是** |
| `06-qwen-agent-framework.py` | 学习代码 | qwen-agent | 通义千问 (DashScope) | **是** |

### 文件详情

#### 06-python-agent-framework.py

**学习第一步：手写 meta-prompt 流程。**

- 依赖：`pip install openai python-dotenv`
- 配置：环境变量 `DASHSCOPE_API_KEY`

核心内容：
- **`generate_system_prompt(role, company, responsibility)`** — 用 meta-prompt 让 LLM 生成详细的 system prompt
- **`test_generated_prompt(system_prompt, test_query)`** — 用生成的 system prompt 测试 Agent 行为
- **三个示例**：航班预订 Agent、技术支持 Agent，展示同一框架在不同场景的复用

meta-prompt 的精髓：你给 LLM 一个"系统提示词生成专家"的角色，它根据你提供的角色/公司/职责自动生成一份结构化的、详尽的 system prompt。这样比手工编写更一致、更可扩展。

#### 06-qwen-agent-framework.py

**学习第二步：用 qwen-agent 框架重写。**

- 依赖：`pip install -U "qwen-agent[gui]"`
- 配置：环境变量 `DASHSCOPE_API_KEY`

对比底层版：
- `Assistant(llm=..., system_message=..., function_list=[])` 封装了消息管理
- 本课的工具列表为空，但不影响框架的价值——消息历史维护、多轮对话等仍由框架处理

## 本课核心概念

- **系统消息框架**：一个 meta-prompt 模板 → 输入角色/公司/职责 → LLM 输出详细的 system prompt
- **元层次设计**：用 LLM 生成 LLM 的指令，提高一致性和可扩展性
- **安全设计**：好的 system prompt 应包含角色边界、操作指南、安全约束、错误处理策略
- **迭代改进**：通过修改基本提示并对比输出，持续优化 system prompt 质量

## 延伸

- 上一课：[05 Agentic RAG](../../05-agentic-rag/README.md)
- 下一课：[07 规划设计](../../07-planning-design/README.md)
