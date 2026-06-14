# 构建可信赖的 AI Agent

## 介绍

本课将涵盖：

- 如何构建和部署安全有效的 AI Agent
- 开发 AI Agent时的重要安全考虑
- 开发 AI Agent时如何维护数据和用户隐私

## 学习目标

完成本课后，您将了解如何：

- 识别和减轻创建 AI Agent时的风险
- 实施安全措施，确保数据和访问权限的正确管理
- 创建维护数据隐私并提供优质用户体验的 AI Agent

## 安全

首先来看如何构建安全的Agent应用。安全意味着 AI Agent按设计执行。作为Agent应用的构建者，我们有方法和工具最大化安全性：

### 构建系统消息框架

如果您曾用大型语言模型（LLM）构建 AI 应用，您会知道设计坚固的系统提示或系统消息有多重要。这些提示设定了元规则、指令和指南，指导 LLM 如何与用户和数据交互。

对于 AI Agent，系统提示更为重要，因为 AI Agent需要极其具体的指令来完成我们为其设计的任务。

为了创建可扩展的系统提示，我们可以使用一个系统消息框架来构建应用中的一个或多个Agent：

#### 步骤 1：创建元系统消息

元提示将被 LLM 用来生成我们创建的Agent的系统提示。我们将其设计为模板，以便高效创建多个Agent（如有需要）。

这是我们给 LLM 的一个元系统消息示例：

```plaintext
你是创建 AI 助手Agent的专家。你将会被提供公司名称、职位、职责及其他信息，这些将用来生成系统提示。为了创建系统提示，请尽可能详细描述，并提供一个结构，让使用大语言模型的系统能够更好地理解 AI 助手的角色和职责。
```

#### 步骤 2：创建基本提示

下一步是创建一个基本提示，描述 AI Agent。您应包括Agent的角色、Agent将完成的任务以及Agent的其他职责。

示例：

```plaintext
你是Contoso Travel的旅行代理，非常擅长为客户预订航班。为了帮助客户，你可以执行以下任务：查找可用航班、预订航班、询问航班的座位和时间偏好、取消之前预订的航班，并在航班延误或取消时提醒客户。
```

#### 步骤 3：向 LLM 提供基本系统消息

现在我们可以通过将元系统消息和我们的基本系统消息一同作为系统消息来优化它。

这将生成一个更适合指导 AI Agent的系统消息：

```markdown
**公司名称:** Contoso Travel  
**角色:** 旅行助手 Agent

**目标：**  
你是Contoso旅游的AI智能旅行Agent，专门负责预订航班并提供优质的客户服务。你的主要目标是帮助客户查找、预订和管理他们的航班，同时确保高效地满足他们的偏好和需求。

**主要职责：**

1. **航班查询:**
    
    - 帮助客户根据他们指定的目的地、日期以及其他相关偏好搜索可用航班。
    - 提供一个选项列表，包括航班时间、航空公司、中途停留和价格。
2. **航班预订:**
    
    - 帮助客户预订机票，确保所有信息都正确输入系统。
    - 确认预订，并向客户提供他们的行程，包括确认号码和其他相关信息。
3. **客户偏好查询:**
    
    - 积极询问客户他们的座位偏好（例如，靠走道、靠窗、额外腿部空间）以及他们喜欢的飞行时间（例如，早晨、下午、晚上）。
    - 记录这些偏好以备将来参考，并据此提供建议。
4. **航班取消：**
    
    - 如果需要，按照公司政策和流程协助客户取消之前预订的航班。
    - 通知客户取消航班可能需要的退款或其他额外步骤。
5. **航班监控：**
    
    - 监控已预订航班的状态，并实时提醒客户关于航班延误、取消或变更的情况。
    - 根据需要通过客户喜欢的沟通渠道（例如电子邮件、短信）提供更新。

**语气和风格：**

- 在与客户的所有互动中保持友好、专业且平易近人的态度。
- 确保所有沟通都清晰、信息充分，并针对客户的具体需求和询问进行调整。

**用户互动说明：**

- 及时且准确地回复客户咨询。
- 在确保专业性的同时，使用对话式的风格。
- 通过在提供帮助时保持细心、同理心和主动性，把客户满意度放在首位。

**附加说明：**

- 关注航空公司政策、旅行限制以及其他可能影响航班预订和客户体验的信息更新。
- 使用清晰简明的语言解释各种选项和流程，尽量避免专业术语，让客户更容易理解。

这个 AI 助手旨在为 Contoso 旅行的客户简化航班预订流程，确保他们的所有旅行需求都能高效、顺利地得到满足。

```

#### 步骤 4：迭代和改进

该系统消息框架的价值在于能够更容易地扩展多Agent系统消息的创建，同时随着时间推移改进系统消息。很少有系统消息能在首次使用时就满足完整用例。通过更改基本系统消息并运行系统，可以进行小幅调整和改进，以便比较和评估结果。

## 理解威胁

要构建可信赖的 AI Agent，了解并缓解对 AI Agent的风险和威胁非常重要。我们只看部分对 AI Agent的不同威胁，以及如何更好地进行规划和准备。

### 任务和指令

**描述：** 攻击者试图通过提示或操纵输入更改 AI Agent的指令或目标。

**缓解措施：** 执行验证检查和输入过滤，检测潜在危险提示，避免其被 AI Agent处理。由于这些攻击通常需要频繁与Agent交互，限制对话轮数也是防止此类攻击的方法。

### 访问关键系统

**描述：** 如果 AI Agent访问存储敏感数据的系统和服务，攻击者可能会破坏Agent与这些服务之间的通信。这些可能是直接攻击，也可能是通过Agent间接获取这些系统信息的尝试。

**缓解措施：** AI Agent应只按需访问系统，以防止此类攻击。Agent与系统间的通信也应保持安全。实施身份验证和访问控制是保护这类信息的另一种方式。

### 资源和服务过载

**描述：** AI Agent可访问不同工具和服务以完成任务。攻击者可利用此能力通过 AI Agent发送大量请求来攻击这些服务，可能导致系统故障或高额费用。

**缓解措施：** 实施策略限制 AI Agent对服务请求次数。限制对话轮数和请求次数也是防止此类攻击的方法。

### 知识库投毒

**描述：** 这类攻击不直接针对 AI Agent，而是针对 AI Agent使用的知识库和其他服务。可能破坏 AI Agent在完成任务时使用的数据或信息，导致对用户产生偏见或意外响应。

**缓解措施：** 定期验证 AI Agent工作流中使用的数据。确保数据访问安全，仅由可信人员更改，以避免此类攻击。

### 级联错误

**描述：** AI Agent访问各种工具和服务以完成任务。攻击者引发的错误可能导致连接系统故障，使攻击范围更广且更难排查。

**缓解措施：** 避免方法之一是让 AI Agent在受限环境中运行，比如在 Docker 容器中执行任务，防止直接系统攻击。创建回退机制和重试逻辑也是防止更大系统故障的方法。

## 人机协作

构建可信赖 AI Agent系统的另一有效方法是利用人机协作。它创建了一个流程，允许用户在运行中向Agent提供反馈。用户本质上充当多Agent系统中的Agent，通过批准或终止运行过程进行交互。

以下代码片段展示使用 Microsoft Agent Framework 实现此概念：

```python
import os
from agent_framework.azure import AzureAIProjectAgentProvider
from azure.identity import AzureCliCredential

# 创建带有人类参与审批的提供者
provider = AzureAIProjectAgentProvider(
    credential=AzureCliCredential(),
)

# 创建带有人类审批步骤的Agent
response = provider.create_response(
    input="Write a 4-line poem about the ocean.",
    instructions="You are a helpful assistant. Ask for user approval before finalizing.",
)

# 用户可以审核并批准响应
print(response.output_text)
user_input = input("Do you approve? (APPROVE/REJECT): ")
if user_input == "APPROVE":
    print("Response approved.")
else:
    print("Response rejected. Revising...")
```

## 结论

构建可信赖的 AI Agent需要精心设计、强健的安全措施和持续迭代。通过实施结构化元提示系统、理解潜在威胁以及应用缓解策略，开发者可以创建既安全又有效的 AI Agent。此外，融入人机协作方式确保 AI Agent始终符合用户需求，同时最小化风险。随着 AI 持续发展，保持对安全、隐私和伦理问题的积极关注，将是培养 AI 驱动系统信任与可靠性的关键。


## 额外资源

- <a href="https://learn.microsoft.com/azure/ai-studio/responsible-use-of-ai-overview" target="_blank">负责任 AI 概述</a>
- <a href="https://learn.microsoft.com/azure/ai-studio/concepts/evaluation-approach-gen-ai" target="_blank">生成式 AI 模型和 AI 应用的评估</a>
- <a href="https://learn.microsoft.com/azure/ai-services/openai/concepts/system-message?context=%2Fazure%2Fai-studio%2Fcontext%2Fcontext&tabs=top-techniques" target="_blank">安全系统消息</a>
- <a href="https://blogs.microsoft.com/wp-content/uploads/prod/sites/5/2022/06/Microsoft-RAI-Impact-Assessment-Template.pdf?culture=en-us&country=us" target="_blank">风险评估模板</a>


## 上一课

[Agentic RAG](../05-agentic-rag/README.md)

## 下一课

[规划设计模式](../07-planning-design/README.md)