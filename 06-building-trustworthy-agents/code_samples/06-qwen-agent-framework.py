"""
Lesson 06 - 构建可信赖 Agent（qwen-agent 框架版）

系统消息框架：用 meta-prompt 让 LLM 生成高质量的系统提示词。
使用 qwen-agent 框架的 Assistant 执行两步生成。

运行前：
  1. 设置环境变量 DASHSCOPE_API_KEY=你的千问APIKey
  2. pip install -U "qwen-agent[gui]"
"""

import os

from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    raise RuntimeError("请设置环境变量 DASHSCOPE_API_KEY")

# ── LLM 配置 ────────────────────────────────────────────

llm_cfg = {
    "model": "qwen-flash",
    "model_type": "qwen_dashscope",
    "api_key": api_key,
}

# ── 系统消息框架 ────────────────────────────────────────

from qwen_agent.agents import Assistant

META_SYSTEM_PROMPT = """你是创建 AI 代理助手的专家。
你将会得到一个公司名称、职位、职责以及其他信息，这些信息将用于生成系统提示。
为了创建系统提示，请尽可能详细描述，并提供一个结构化的格式，让使用大语言模型的系统能够更好地理解 AI 助手的角色和职责。"""


def run_once(agent: Assistant, user_query: str) -> str:
    """运行一次对话，返回完整回复文本。"""
    messages = [{"role": "user", "content": user_query}]
    response_text = ""
    for responses in agent.run(messages=messages):
        if responses:
            last = responses[-1]
            if last.get("role") == "assistant" and last.get("content"):
                response_text = last["content"]
    return response_text


def generate_system_prompt(role: str, company: str, responsibility: str) -> str:
    """使用 meta-prompt 生成详细的系统提示词。"""
    generator = Assistant(
        llm=llm_cfg,
        name="SystemPromptGenerator",
        system_message=META_SYSTEM_PROMPT,
        function_list=[],  # 不需要工具
    )
    return run_once(
        generator,
        f"You are a {role} at {company} that is responsible for {responsibility}.",
    )


def test_generated_prompt(system_prompt: str, test_query: str) -> str:
    """用生成的系统提示词测试 Agent 行为。"""
    tester = Assistant(
        llm=llm_cfg,
        name="TestAgent",
        system_message=system_prompt,
        function_list=[],
    )
    return run_once(tester, test_query)


# ── 运行示例 ────────────────────────────────────────────

if __name__ == "__main__":
    # ─── 示例 1：生成旅行代理的系统提示词 ───
    print("=" * 60)
    print("示例 1：为 Contoso Travel 的航班预订 Agent 生成系统提示词")
    print("=" * 60)

    generated_prompt = generate_system_prompt(
        role="旅行助手",
        company="Contoso Travel",
        responsibility="机票订购",
    )
    print(generated_prompt)
    print()

    # ─── 示例 2：用生成的提示词测试 Agent ───
    print("=" * 60)
    print("示例 2：用生成的系统提示词回答用户问题")
    print("=" * 60)
    answer = test_generated_prompt(
        system_prompt=generated_prompt,
        test_query="我下周一需要从北京飞东京，周五返回。我有什么选择吗？",
    )
    print(answer)
    print()

    # ─── 示例 3：生成技术支持 Agent 的系统提示词 ───
    print("=" * 60)
    print("示例 3：为技术支持 Agent 生成系统提示词")
    print("=" * 60)
    tech_prompt = generate_system_prompt(
        role="技术支持专家",
        company="CloudServe Inc.",
        responsibility="帮助客户排查云基础设施问题",
    )
    print(tech_prompt)
