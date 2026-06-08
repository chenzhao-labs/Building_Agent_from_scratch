## 介绍

本节内容包括：

- 什么是 AI Agents，以及不同类型的 AI Agents
- AI Agents 最适合处理的任务类型
- 设计Agents解决方案时的核心构建模块

## 学习目标

完成本节后，你应该能够：

- 解释 AI Agents 的概念及其与普通 AI 解决方案的区别
- 了解何时应选择使用 AI Agents（以及何时不该使用）
- 绘制针对实际问题的基本Agents解决方案设计草图

---

## AI Agents 及 Agents 类型定义

### 什么是 AI Agents？

简单来说：

> **AI Agents 是让大型语言模型（LLM）真正“做事”的系统——通过赋予它们工具和知识，来作用于现实世界，而不仅仅是响应提示。**

具体拆解：

- <strong>系统</strong> — AI Agents 不是单一事物，而是多个部分协同工作的集合。每个Agents核心包含三部分：
  - <strong>环境</strong> — Agents工作的空间。对于旅游预订Agents，它就是预订平台本身。
  - <strong>传感器</strong> — Agents感知当前环境状态的方式。我们的旅游Agents会检查酒店可用性或机票价格。
  - <strong>执行器</strong> — Agents采取行动的方式。旅游Agents可能预订房间、发送确认或取消预订。

- <strong>大型语言模型</strong> — Agents在 LLM 出现前就存在，但 LLM 让现代Agents更加强大。它们能理解自然语言、推理上下文，将模糊的用户请求转化为具体行动计划。

- <strong>执行动作</strong> — 没有Agents系统，LLM 只有生成文本的能力。置于Agents系统中，LLM 能真正执行步骤——搜索数据库、调用 API、发送消息。

- <strong>接入工具</strong> — Agents可用的工具取决于（1）其运行环境，（2）开发提供了哪些工具。旅游Agents可能能搜索航班但不能修改客户记录——这取决于你的配置。

- **记忆 + 知识** — Agents可拥有短期记忆（当前对话）和长期记忆（客户数据库、过往交互）。旅游Agents可能“记得”你偏好靠窗座位。

---

### 不同类型的 AI Agents

Agents类型各异，以下用旅游预订Agents作为例子：

| <strong>Agents 类型</strong> | <strong>功能描述</strong> | <strong>旅游Agents示例</strong> |
|---|---|---|
| <strong>简单反射Agents</strong> | 遵循硬编码规则——无记忆，无规划。 | 看到投诉邮件→转发客服。仅此而已。 |
| <strong>基于模型的反射Agents</strong> | 内部维护世界模型，并随变化更新。 | 跟踪历史机票价格，标记突然昂贵的航线。 |
| <strong>基于目标的Agents</strong> | 有具体目标，逐步策划达成路径。 | 预订完整行程（机票、租车、酒店），从你所在地到目的地。 |
| <strong>基于效用的Agents</strong> | 不仅找到「一个」方案，而是权衡得到「最佳」方案。 | 平衡费用与便利性，找到最符合偏好的行程。 |
| <strong>学习型Agents</strong> | 通过反馈不断学习并改进。 | 根据旅行后调查结果调整未来推荐。 |
| <strong>层级Agents</strong> | 高层Agents分解任务，委派底层Agents完成。 | “取消行程”请求拆分为取消机票、取消酒店、取消租车，由子Agents处理。 |
| **多Agents系统（MAS）** | 多个独立Agents协作（或竞争）。 | 协作：不同Agents负责酒店、航班和娱乐。竞争：多个Agents争夺最优酒店房价。 |

---

## 何时使用 AI Agents

能用 AI Agents 不代表总该用。Agents真正发光的场景包括：

- <strong>开放式问题</strong> — 解决步骤无法预编程，需要 LLM 动态寻找路径。
- <strong>多步骤流程</strong> — 需跨多轮使用工具，而非单次查询或生成。
- <strong>持续改进</strong> — 希望系统基于用户反馈或环境信号不断变聪明。

本课程后续的 **构建可信赖的 AI Agents** 章节会更深入探讨何时适合（或不适合）使用 AI Agents。

---

## Agents解决方案基础

### Agents开发

构建Agents的首要任务是定义Agents能做什么——其工具、动作和行为。

### Agents模式

与 LLM 通信依赖提示。Agents需要跨多步骤行动，不能手工逐条设计所有提示。这时就用上了<strong>Agents理模式</strong>，它是可复用的提示与调度策略，助你更高效、可靠地组织 LLM 工作。

本课程围绕最常用和最实用的Agents模式展开。

### Agents框架

Agents框架为开发者提供现成模板、工具和基础设施，简化：

- 工具与功能的整合
- 观察Agents运行状态（及调试问题）
- 多Agents协作开发

---

## 代码示例

准备好实践了吗？本节的代码示例：

- 🐍 Python: [Agent Framework](./code_samples/01-python-agent-framework.py)

---

## 下一节

[探索Agents框架](../02-explore-agentic-frameworks/README.md)

---

<!-- CO-OP TRANSLATOR DISCLAIMER START -->
**参考**：microsoft/ai-agents-for-beginners
<!-- CO-OP TRANSLATOR DISCLAIMER END -->