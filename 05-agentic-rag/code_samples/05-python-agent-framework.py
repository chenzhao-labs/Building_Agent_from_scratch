"""
Lesson 05 - Agentic RAG（通义千问适配版 · 原生 openai SDK）

用 openai SDK 直连通义千问 API，手动实现 tool calling 循环。
演示：1) 基础 Agentic RAG（Agent 自主决定何时检索）
      2) 迭代制作者-检查者模式（Producer-Checker）

运行前：
  1. 设置环境变量 DASHSCOPE_API_KEY=你的千问APIKey
  2. pip install openai python-dotenv
"""

import json
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
MODEL = "qwen-max"


# ── 知识库 ──────────────────────────────────────────────

TRAVEL_KNOWLEDGE_BASE = {
    "巴塞罗那": "巴塞罗那是西班牙加泰罗尼亚的国际化首都。最佳访问时间为3月至5月或9月至11月。以高迪建筑、兰布拉大道和海滩而闻名。平均每日费用：150-200美元。",
    "东京": "东京是日本的首都，将超现代与传统相结合。最佳旅游时间是三月至四月（樱花季）或十月至十一月。以涩谷、寺庙、寿司闻名。日均花费：200-250美元。",
    "巴黎": "巴黎是法国的首都，也是全球艺术、时尚和文化的中心。最佳旅游时间是四月至六月或九月至十月。以埃菲尔铁塔、卢浮宫和美食而闻名。平均每日花费：180-250美元。",
    "开普敦": "开普敦位于南非西南端。最佳旅游时间为11月至3月。以桌山、葡萄酒产区和野生动物而闻名。平均每日花费：100-150美元。",
}


# ── 搜索工具 ────────────────────────────────────────────

def search_travel_knowledge(query: str) -> str:
    """在旅游知识库中搜索目的地信息。"""
    results = []
    for destination, info in TRAVEL_KNOWLEDGE_BASE.items():
        if query.lower() in destination.lower() or any(
            word in info.lower() for word in query.lower().split()
        ):
            results.append(f"**{destination}**: {info}")
    return (
        "\n\n".join(results) if results else "No matching destinations found in the knowledge base."
    )


TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_travel_knowledge",
            "description": "搜索旅游知识库获取目的地信息，包括最佳旅行时间、特色、日均费用等",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "关于旅游目的地的搜索查询，可以是目的地名称或关键词",
                    },
                },
                "required": ["query"],
            },
        },
    },
]

TOOL_MAP = {
    "search_travel_knowledge": search_travel_knowledge,
}


# ── Tool Calling 循环 ───────────────────────────────────

def _assistant_message(msg) -> dict:
    """把 openai SDK 的 message 对象转为 messages 列表可用的 dict。"""
    return {
        "role": "assistant",
        "content": msg.content,
        "tool_calls": [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in msg.tool_calls
        ],
    }


def run_agent(system_prompt: str, user_message: str) -> str:
    """运行 agent，自动处理 tool calling 循环。"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS_SCHEMA,
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content

        # 有 tool_calls → 执行工具，结果追加到对话
        print(f"  [Agent 调用工具] {[tc.function.name for tc in msg.tool_calls]}")
        messages.append(_assistant_message(msg))

        for tc in msg.tool_calls:
            func = TOOL_MAP.get(tc.function.name)
            if func:
                args = json.loads(tc.function.arguments)
                result = func(**args)
            else:
                result = f"未知工具: {tc.function.name}"
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })


# ── 运行示例 ────────────────────────────────────────────

if __name__ == "__main__":
    # ─── 示例 1：基础 Agentic RAG ───
    # Agent 被指示在回答前始终先检索知识库
#     print("=" * 60)
#     print("示例 1：基础 Agentic RAG — Agent 自主检索")
#     print("=" * 60)
#     result = run_agent(
#         """你是一个知识渊博的旅行顾问。在回答关于目的地的问题之前：
# 1. 始终先使用 search_travel_knowledge 工具搜索旅行知识库
# 2. 根据检索到的信息提供答案
# 3. 如果知识库中没有相关信息，要明确说明
# 4. 提供具体细节，如费用、最佳季节和亮点。
# 5. 最终的回答只能基于知识库知识
# 请用中文回复。""",
#         "我对参观拥有建筑（高迪建筑）的地方很感兴趣。你会推荐哪些目的地？",
#     )
#     print(result)
#     print()

    # ─── 示例 2：迭代制作者-检查者模式 ───
    # Agent 被指示先搜索 → 用目的地名再次搜索获取完整详情 → 比较验证
    print("=" * 60)
    print("示例 2：Producer-Checker 模式 — 迭代检索验证")
    print("=" * 60)
    result = run_agent(
        """你是一位一丝不苟的旅行顾问，会仔细核对推荐内容。  
在回答旅行问题时：  
1. 首先搜索相关目的地  
2. 对每个找到的目的地，再次以目的地名称进行搜索以获取完整信息  
3. 使用经过验证的信息比较各个选项  
4. 提出最终推荐，包括具体费用、最佳旅行时间和亮点  
5. 如果任何细节似乎不完整，再次搜索确认后再回答。 
6. 最终的回答只能基于知识库知识 
请用中文回复。""",
        "我的预算是每天175美元，并且想在四月旅行。哪些目的地适合我的预算和时间安排？",
    )
    print(result)
