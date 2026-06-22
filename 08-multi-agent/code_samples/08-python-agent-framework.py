"""
Lesson 08 - 多Agent设计模式（LangGraph + 原生 OpenAI SDK 版）

本课覆盖多Agent编排的三种核心模式：
  1. 流水线式 (Sequential)  — Agent 按顺序执行，上游输出→下游输入
  2. 并发式   (Concurrent)  — 多个 Agent 同时执行，结果汇总
  3. 条件式   (Conditional)  — 根据中间结果动态选择下游路径

用 LangGraph 的 StateGraph / Send / conditional_edges 实现上述三种模式。

运行前：
  1. 设置环境变量 DASHSCOPE_API_KEY=你的千问APIKey
  2. pip install openai langgraph python-dotenv
"""

import operator
import os
from typing import Annotated, Optional

from dotenv import load_dotenv
from openai import OpenAI
from langgraph.graph import END, StateGraph, Send
from typing import TypedDict

load_dotenv()

api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    raise RuntimeError("请设置环境变量 DASHSCOPE_API_KEY（https://bailian.console.aliyun.com/）")

client = OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
MODEL = "qwen-plus"


# ═══════════════════════════════════════════════════════════
# 通用工具函数
# ═══════════════════════════════════════════════════════════

def _call_llm(system_prompt: str, user_content: str, agent_label: str) -> str:
    """调用 LLM 并流式输出到终端，返回完整文本。"""
    print(f"\n{'='*50}")
    print(f"🤖 {agent_label}:")
    print(f"{'='*50}")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    full = ""
    stream = client.chat.completions.create(
        model=MODEL, messages=messages, stream=True,
    )
    for chunk in stream:
        if chunk.choices[0].delta.content:
            text = chunk.choices[0].delta.content
            print(text, end="", flush=True)
            full += text
    print()
    return full


# ═══════════════════════════════════════════════════════════
# 模式 1：流水线式 (Sequential)
#
# 场景：家具采购三阶段
#   Sales-Agent → Price-Agent → Quote-Agent
#
# 每个Agent的输出是下一个Agent的输入。
# 在 LangGraph 中，最简单的 add_edge 链即可实现。
# ═══════════════════════════════════════════════════════════

SALES_AGENT_INSTRUCTIONS = """\
你是一名家具销售顾问。根据客户对房间和风格偏好的描述，推荐具体的家具。对于每件家具，包含风格、材质和主要特点。用中文回复。"""

PRICE_AGENT_INSTRUCTIONS = """\
你是一名家具定价专家。根据推荐的家具清单，为每件物品提供合理的价格区间。包括经济实惠的替代品和高端选项。估算总成本。用中文回复。"""

QUOTE_AGENT_INSTRUCTIONS = """\
你是一名采购助理，负责制作正式的采购报价。根据家具推荐和价格分析，制作一份结构清晰的报价单，其中包括分项费用、小计、预计交货时间和总计。请用中文回复。"""


class SequentialState(TypedDict):
    user_query: str
    sales_recommendation: Optional[str]
    price_analysis: Optional[str]
    quote: Optional[str]


def sales_node(state: SequentialState) -> dict:
    rec = _call_llm(SALES_AGENT_INSTRUCTIONS, state["user_query"], "Sales-Agent")
    return {"sales_recommendation": rec}


def price_node(state: SequentialState) -> dict:
    prompt = (
        f"客户需求：{state['user_query']}\n\n"
        f"家具推荐：\n{state['sales_recommendation']}\n\n"
        "请为以上每件家具提供价格区间、平价替代方案和总费用估算。"
    )
    analysis = _call_llm(PRICE_AGENT_INSTRUCTIONS, prompt, "Price-Agent")
    return {"price_analysis": analysis}


def quote_node(state: SequentialState) -> dict:
    prompt = (
        f"客户需求：{state['user_query']}\n\n"
        f"家具推荐：\n{state['sales_recommendation']}\n\n"
        f"价格分析：\n{state['price_analysis']}\n\n"
        "请生成一份正式报价单，逐项列出费用。"
    )
    q = _call_llm(QUOTE_AGENT_INSTRUCTIONS, prompt, "Quote-Agent")
    return {"quote": q}


def demo_1_sequential():
    print("=" * 60)
    print("模式 1：流水线式 — Sales → Price → Quote")
    print("=" * 60)

    graph = StateGraph(SequentialState)
    graph.add_node("sales", sales_node)
    graph.add_node("price", price_node)
    graph.add_node("quote", quote_node)
    graph.add_edge("sales", "price")
    graph.add_edge("price", "quote")
    graph.add_edge("quote", END)
    graph.set_entry_point("sales")
    app = graph.compile()

    initial: SequentialState = {
        "user_query": (
            "我正在用温暖、舒适的风格布置一个现代客厅： "
            "一张舒适的三人沙发，两把装饰扶手椅，一张木质咖啡桌， "
            "一个电视柜、一盏落地灯和一块柔软的地毯。"
        ),
        "sales_recommendation": None, "price_analysis": None, "quote": None,
    }
    for _ in app.stream(initial):
        pass
    print()


# ═══════════════════════════════════════════════════════════
# 模式 2：并发式 (Concurrent / Fan-out)
#
# 场景：旅行规划 — 研究 + 规划并行
#   Dispatcher → Researcher ‖ Planner → (各输出独立结果)
#
# LangGraph 中用 Send API 实现 fan-out：
#   条件边函数返回多个 Send 对象，分别指向不同节点。
#   每个节点独立修改 state，通过 reducer (operator.add) 合并结果。
# ═══════════════════════════════════════════════════════════

RESEARCHER_INSTRUCTIONS = """\
你是一名旅行研究员。分析目的地，列出相关景点、当地风俗、天气注意事项，并对每个景点做详细观察。用中文回复。"""

PLANNER_INSTRUCTIONS = """\
你是一名旅行策划师。根据目的地，制定一个详细的每日行程安排，包括时间分配、交通建议和餐饮推荐。请用中文回复。"""


class ConcurrentState(TypedDict):
    user_query: str
    # reducer=operator.add 会把每个 Agent 输出的字符串追加到 list
    results: Annotated[list, operator.add]


def dispatcher_node(state: ConcurrentState) -> dict:
    """不调用 LLM，只是把任务分发到两个 Agent。"""
    print(f"\n📋 任务分发: {state['user_query']}")
    print("   → Researcher ‖ Planner（并行执行）")
    return {}


def researcher_node(state: ConcurrentState) -> dict:
    """研究员：分析目的地、景点、文化、天气。"""
    result = _call_llm(RESEARCHER_INSTRUCTIONS, state["user_query"], "Researcher-Agent")
    label = "\n--- Researcher 输出 ---\n" + result
    return {"results": [label]}


def planner_node(state: ConcurrentState) -> dict:
    """规划师：制定每日行程、交通、餐饮。"""
    result = _call_llm(PLANNER_INSTRUCTIONS, state["user_query"], "Plan-Agent")
    label = "\n--- Planner 输出 ---\n" + result
    return {"results": [label]}


def fan_out_to_agents(state: ConcurrentState) -> list[Send]:
    """将同一状态广播到两个Agent节点。"""
    return [
        Send("researcher", {"user_query": state["user_query"], "results": []}),
        Send("planner", {"user_query": state["user_query"], "results": []}),
    ]


def aggregate_node(state: ConcurrentState) -> dict:
    """汇聚节点：展示所有并行结果。"""
    print(f"\n{'='*50}")
    print("📊 汇聚结果（两个Agent的输出已收集完毕）")
    print(f"{'='*50}")
    for i, r in enumerate(state["results"], 1):
        print(r)
    return {}


def demo_2_concurrent():
    print("=" * 60)
    print("模式 2：并发式 — Researcher ‖ Planner（Fan-out → Aggregate）")
    print("=" * 60)

    graph = StateGraph(ConcurrentState)
    graph.add_node("dispatcher", dispatcher_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("planner", planner_node)
    graph.add_node("aggregate", aggregate_node)

    graph.set_entry_point("dispatcher")
    # 关键：用 conditional_edges + Send 列表实现 fan-out
    graph.add_conditional_edges("dispatcher", fan_out_to_agents)
    # 并行节点完成后汇聚到一个节点
    graph.add_edge("researcher", "aggregate")
    graph.add_edge("planner", "aggregate")
    graph.add_edge("aggregate", END)

    app = graph.compile()

    initial: ConcurrentState = {
        "user_query": "Plan a trip to Tokyo in December, interested in technology and food.",
        "results": [],
    }
    for _ in app.stream(initial):
        pass
    print()


# ═══════════════════════════════════════════════════════════
# 模式 3：条件式 (Conditional)
#
# 场景：内容审核流水线
#   Writer → Reviewer → (通过 → Publisher / 不通过 → Writer 重写)
#
# LangGraph 中用 add_conditional_edges 实现分支：
#   路由函数根据 state 中的审核结果决定下一步走哪条边。
# ═══════════════════════════════════════════════════════════

WRITER_INSTRUCTIONS = """\
你是一名技术内容撰稿人。根据给定的大纲写一篇简短的教程草稿。草稿必须超过200字。以纯文本形式输出草稿。
请用中文回复。"""

REVIEWER_INSTRUCTIONS = """\
你是内容审核员。检查草稿是否符合要求：
- 如果草稿超过200字：准确回复“PASS”，并附上简短评论。
- 如果草稿少于200字：准确回复“REVISE”，并说明原因。
你的回复开头必须在第一行写上“PASS”或“REVISE”。"""

PUBLISHER_INSTRUCTIONS = """\
你是一名内容发布者。草稿已经通过审核。宣布内容已发布，漂亮地排版，并总结关键要点。以轻松的语气回复。"""


class ConditionalState(TypedDict):
    outline: str
    draft: Optional[str]
    review_result: Optional[str]  # "PASS" or "REVISE"
    iteration: int  # 防止无限循环


def writer_node(state: ConditionalState) -> dict:
    """Writer: 根据大纲撰写初稿。"""
    prompt = state["outline"]
    if state["draft"] and state["review_result"] == "REVISE":
        prompt = (
            f"你的上一稿被驳回。请根据以下意见修改重写：\n\n"
            f"原稿：\n{state['draft']}\n\n"
            f"根据大纲重新撰写，确保超过 200 字：\n{state['outline']}"
        )
    draft = _call_llm(WRITER_INSTRUCTIONS, prompt, f"Writer-Agent (第{state['iteration'] + 1}轮)")
    return {"draft": draft, "iteration": state["iteration"] + 1}


def reviewer_node(state: ConditionalState) -> dict:
    """Reviewer: 审核稿件的字数是否达标。"""
    prompt = f"请审核以下稿件是否超过 200 字：\n\n{state['draft']}"
    result = _call_llm(REVIEWER_INSTRUCTIONS, prompt, "Reviewer-Agent")
    # 解析 PASS / REVISE
    first_line = result.strip().split("\n")[0].upper()
    if "PASS" in first_line:
        return {"review_result": "PASS"}
    return {"review_result": "REVISE"}


def publisher_node(state: ConditionalState) -> dict:
    """Publisher: 发布通过审核的内容。"""
    prompt = f"以下内容已通过审核，请宣布发布并总结要点：\n\n{state['draft']}"
    result = _call_llm(PUBLISHER_INSTRUCTIONS, prompt, "Publisher-Agent")
    return {}


def route_after_review(state: ConditionalState) -> str:
    """条件路由：通过→发布，不通过→重写。最多重写 3 轮。"""
    if state["review_result"] == "PASS":
        return "publisher"
    if state["iteration"] >= 3:
        print("\n⚠️  已达最大重写次数(3轮)，强制发布。")
        return "publisher"
    print(f"\n🔄 稿件未通过审核（第{state['iteration']}轮），返回 Writer 重写...")
    return "writer"


def demo_3_conditional():
    print("=" * 60)
    print("模式 3：条件式 — Writer → Reviewer → (PASS→Publisher / REVISE→重写)")
    print("=" * 60)

    graph = StateGraph(ConditionalState)
    graph.add_node("writer", writer_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("publisher", publisher_node)

    graph.set_entry_point("writer")
    graph.add_edge("writer", "reviewer")
    graph.add_conditional_edges(
        "reviewer",
        route_after_review,
        {"writer": "writer", "publisher": "publisher"},
    )
    graph.add_edge("publisher", END)

    app = graph.compile()

    initial: ConditionalState = {
        "outline": "写一篇关于 AI Agent 中 Tool Calling 机制的入门教程。",
        "draft": None,
        "review_result": None,
        "iteration": 0,
    }
    for _ in app.stream(initial):
        pass
    print()


# ═══════════════════════════════════════════════════════════
# 运行所有示例
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    demo_1_sequential()
    demo_2_concurrent()
    demo_3_conditional()
