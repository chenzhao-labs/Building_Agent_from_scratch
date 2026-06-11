"""
Lesson 05 - Agentic RAG（qwen-agent 框架版）

使用 qwen-agent 框架调用通义千问 API。
演示：1) 基础 Agentic RAG   2) 迭代制作者-检查者模式

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

# ── 知识库 ──────────────────────────────────────────────

TRAVEL_KNOWLEDGE_BASE = {
    "巴塞罗那": "巴塞罗那是西班牙加泰罗尼亚的国际化首都。最佳访问时间为3月至5月或9月至11月。以高迪建筑、兰布拉大道和海滩而闻名。平均每日费用：150-200美元。",
    "东京": "东京是日本的首都，将超现代与传统相结合。最佳旅游时间是三月至四月（樱花季）或十月至十一月。以涩谷、寺庙、寿司闻名。日均花费：200-250美元。",
    "巴黎": "巴黎是法国的首都，也是全球艺术、时尚和文化的中心。最佳旅游时间是四月至六月或九月至十月。以埃菲尔铁塔、卢浮宫和美食而闻名。平均每日花费：180-250美元。",
    "开普敦": "开普敦位于南非西南端。最佳旅游时间为11月至3月。以桌山、葡萄酒产区和野生动物而闻名。平均每日花费：100-150美元。",
}


# ── 搜索工具 ────────────────────────────────────────────

from qwen_agent.tools.base import BaseTool, register_tool


@register_tool("search_travel_knowledge")
class SearchTravelKnowledge(BaseTool):
    description = "搜索旅游知识库获取目的地信息，包括最佳旅行时间、特色、日均费用等"
    parameters = [
        {
            "name": "query",
            "type": "string",
            "description": "关于旅游目的地的搜索查询，可以是目的地名称或关键词",
            "required": True,
        },
    ]

    def call(self, params: str, **kwargs) -> str:
        import json
        args = json.loads(params) if isinstance(params, str) else params
        query = args.get("query", "")
        results = []
        for destination, info in TRAVEL_KNOWLEDGE_BASE.items():
            if query.lower() in destination.lower() or any(
                word in info.lower() for word in query.lower().split()
            ):
                results.append(f"**{destination}**: {info}")
        return (
            "\n\n".join(results)
            if results
            else "No matching destinations found in the knowledge base."
        )


# ── Agent 运行辅助 ──────────────────────────────────────

from qwen_agent.agents import Assistant


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


# ── 运行示例 ────────────────────────────────────────────

if __name__ == "__main__":
    # ─── 示例 1：基础 Agentic RAG ───
    print("=" * 60)
    print("示例 1：基础 Agentic RAG — Agent 自主检索")
    print("=" * 60)
    rag_agent = Assistant(
        llm=llm_cfg,
        name="TravelRAGAgent",
        system_message=(
             """你是一个知识渊博的旅行顾问。在回答关于目的地的问题之前：
            1. 始终先使用 search_travel_knowledge 工具搜索旅行知识库
            2. 根据检索到的信息提供答案
            3. 如果知识库中没有相关信息，要明确说明
            4. 提供具体细节，如费用、最佳季节和亮点。
            5. 最终的回答只能基于知识库知识
            请用中文回复。"""
        ),
        function_list=["search_travel_knowledge"],
    )
    result = run_once(
        rag_agent,
        "我对参观拥有建筑（高迪建筑）的地方很感兴趣。你会推荐哪些目的地？",
    )
    print(result)
    print()

    # ─── 示例 2：迭代制作者-检查者模式 ───
    print("=" * 60)
    print("示例 2：Producer-Checker 模式 — 迭代检索验证")
    print("=" * 60)
    checker_agent = Assistant(
        llm=llm_cfg,
        name="TravelRAGCheckerAgent",
        system_message=(
            """你是一位一丝不苟的旅行顾问，会仔细核对推荐内容。  
            在回答旅行问题时：  
            1. 首先搜索相关目的地  
            2. 对每个找到的目的地，再次以目的地名称进行搜索以获取完整信息  
            3. 使用经过验证的信息比较各个选项  
            4. 提出最终推荐，包括具体费用、最佳旅行时间和亮点  
            5. 如果任何细节似乎不完整，再次搜索确认后再回答。 
            6. 最终的回答只能基于知识库知识 
            请用中文回复。"""
        ),
        function_list=["search_travel_knowledge"],
    )
    result = run_once(
        checker_agent,
        "我的预算是每天175美元，并且想在四月旅行。哪些目的地适合我的预算和时间安排？",
    )
    print(result)
