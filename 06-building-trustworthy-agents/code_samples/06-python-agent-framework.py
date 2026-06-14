"""
Lesson 06 - 构建可信赖 Agent

系统消息框架：用 meta-prompt 让 LLM 生成高质量的系统提示词。
不依赖任何 Agent 框架，直接使用 openai SDK。

核心理念：与其手工编写系统提示词，不如让 LLM 帮你生成——
给 LLM 一个"系统提示词生成专家"的角色，输入你的需求，它输出精心设计的 system prompt。

运行前：
  1. 设置环境变量 DASHSCOPE_API_KEY=你的千问APIKey
  2. pip install openai python-dotenv
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ── 连接千问 ────────────────────────────────────────────

api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    raise RuntimeError("请设置环境变量 DASHSCOPE_API_KEY（在百炼平台获取：https://bailian.console.aliyun.com/）")

client = OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
MODEL = "qwen-flash"


# ── 系统消息框架 ────────────────────────────────────────
# 这是一个 "meta-prompt"：让 LLM 扮演"系统提示词生成专家"，
# 根据你提供的角色/公司/职责，自动生成一份详尽的 system prompt。

META_SYSTEM_PROMPT = """你是创建 AI 代理助手的专家。
你将会得到一个公司名称、职位、职责以及其他信息，这些信息将用于生成系统提示。
为了创建系统提示，请尽可能详细描述，并提供一个结构化的格式，让使用大语言模型的系统能够更好地理解 AI 助手的角色和职责。"""


def generate_system_prompt(role: str, company: str, responsibility: str) -> str:
    """使用 meta-prompt 生成详细的系统提示词。

    Args:
        role: AI 助手的角色（如 "travel agent"）
        company: 公司名称（如 "Contoso Travel"）
        responsibility: 主要职责（如 "booking flights"）

    Returns:
        LLM 生成的详细系统提示词
    """
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": META_SYSTEM_PROMPT},
            {"role": "user", "content": f"You are a {role} at {company} that is responsible for {responsibility}."},
        ],
        temperature=1.0,
        max_tokens=1000,
        top_p=1.0,
    )
    return response.choices[0].message.content


# ── 验证：用生成的系统提示词运行 Agent ──────────────────
# 拿到生成的系统提示词后，可以让同一个 LLM 扮演这个角色来验证效果

def test_generated_prompt(system_prompt: str, test_query: str) -> str:
    """用生成的系统提示词测试 Agent 行为。"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": test_query},
        ],
    )
    return response.choices[0].message.content


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

    # ─── 示例 3：生成另一种角色的系统提示词 ───
    print("=" * 60)
    print("示例 3：为技术支持 Agent 生成系统提示词")
    print("=" * 60)
    tech_prompt = generate_system_prompt(
        role="技术支持专家",
        company="CloudServe Inc.",
        responsibility="帮助客户排查云基础设施问题",
    )
    print(tech_prompt)
