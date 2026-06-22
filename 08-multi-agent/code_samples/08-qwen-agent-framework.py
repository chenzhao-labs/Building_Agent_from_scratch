"""
Lesson 08 - 多Agent设计模式（qwen-agent 框架版）

用 qwen-agent 的 Assistant 类实现三种核心编排模式：
  1. 流水线式 (Sequential)  — 手动链式调用，上游输出→下游输入
  2. 并发式   (Concurrent)  — asyncio.gather 并行执行多个 Assistant
  3. 条件式   (Conditional)  — 解析中间结果，if/else 决定下游路径

运行前：
  1. 设置环境变量 DASHSCOPE_API_KEY=你的千问APIKey
  2. pip install -U "qwen-agent[gui]" python-dotenv
"""

import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    raise RuntimeError("请设置环境变量 DASHSCOPE_API_KEY（https://bailian.console.aliyun.com/）")

llm_cfg = {
    "model": "qwen-plus",
    "model_type": "qwen_dashscope",
    "api_key": api_key,
}


# ═══════════════════════════════════════════════════════════
# 通用工具
# ═══════════════════════════════════════════════════════════

from qwen_agent.agents import Assistant


def run_agent(agent: Assistant, user_query: str, label: str = "") -> str:
    """运行 agent 一轮，流式输出，返回最终文本。"""
    if label:
        print(f"\n{'='*50}")
        print(f"🤖 {label}:")
        print(f"{'='*50}")

    messages = [{"role": "user", "content": user_query}]
    response_text = ""
    for responses in agent.run(messages=messages):
        if responses:
            last = responses[-1]
            if last.get("role") == "assistant" and last.get("content"):
                new_content = last["content"]
                if len(new_content) > len(response_text):
                    print(new_content[len(response_text):], end="", flush=True)
                response_text = new_content
    print()
    return response_text


async def run_agent_async(agent: Assistant, user_query: str) -> str:
    """异步版：用于并发场景。"""
    messages = [{"role": "user", "content": user_query}]
    response_text = ""
    for responses in agent.run(messages=messages):
        if responses:
            last = responses[-1]
            if last.get("role") == "assistant" and last.get("content"):
                response_text = last["content"]
    return response_text


# ═══════════════════════════════════════════════════════════
# Agent 系统提示
# ═══════════════════════════════════════════════════════════

# --- 流水线模式 ---
SALES_INSTRUCTIONS = """\
你是一名家具销售顾问。根据客户对房间和风格偏好的描述，推荐具体的家具。对于每件家具，包含风格、材质和主要特点。用中文回复。"""

PRICE_INSTRUCTIONS = """\
你是一名家具定价专家。根据推荐的家具清单，为每件物品提供合理的价格区间。包括经济实惠的替代品和高端选项。估算总成本。用中文回复。"""

QUOTE_INSTRUCTIONS = """\
你是一名采购助理，负责制作正式的采购报价。根据家具推荐和价格分析，制作一份结构清晰的报价单，其中包括分项费用、小计、预计交货时间和总计。用中文回复。"""

# --- 并发模式 ---
RESEARCHER_INSTRUCTIONS = """\
你是一名旅行研究员。分析目的地，列出相关景点、当地风俗、天气注意事项，并对每个景点做详细观察。用中文回复。"""

PLANNER_INSTRUCTIONS = """\
你是一名旅行策划师。根据目的地，制定一个详细的每日行程安排，包括时间分配、交通建议和餐饮推荐。用中文回复。"""

# --- 条件模式 ---
WRITER_INSTRUCTIONS = """\
你是一名技术内容撰稿人。根据给定的大纲写一篇简短的教程草稿。草稿必须超过200字。以纯文本形式输出草稿。请用中文回复。"""

REVIEWER_INSTRUCTIONS = """\
你是内容审核员。检查草稿是否符合要求：
- 如果草稿超过200字：准确回复“PASS”，并附上简短评论。
- 如果草稿少于200字：准确回复“REVISE”，并说明原因。
你的回复开头必须在第一行写上“PASS”或“REVISE”。"""

PUBLISHER_INSTRUCTIONS = """\
你是一名内容发布者。草稿已经通过审核。请宣布内容已发布，排版美观，并总结关键要点。用中文回复。"""


# ═══════════════════════════════════════════════════════════
# 模式 1：流水线式 (Sequential)
#
# 手动链式调用。每个 Agent 的输出作为下一个的输入。
# 和 LangGraph add_edge 链本质相同，只是手动传递上下文。
# ═══════════════════════════════════════════════════════════

def demo_1_sequential():
    print("=" * 60)
    print("模式 1：流水线式 — Sales → Price → Quote（手动链式调用）")
    print("=" * 60)

    sales = Assistant(llm=llm_cfg, name="Sales-Agent", system_message=SALES_INSTRUCTIONS)
    price = Assistant(llm=llm_cfg, name="Price-Agent", system_message=PRICE_INSTRUCTIONS)
    quote = Assistant(llm=llm_cfg, name="Quote-Agent", system_message=QUOTE_INSTRUCTIONS)

    user_query = (
        "I am furnishing a modern living room with warm, inviting style: "
        "a comfortable three-seat sofa, two accent armchairs, a wooden coffee table, "
        "a TV stand, a floor lamp, and a soft area rug."
    )

    # Step 1: Sales 推荐
    rec = run_agent(sales, user_query, "Sales-Agent")

    # Step 2: Price 定价
    price_input = (
        f"客户需求：{user_query}\n\n家具推荐：\n{rec}\n\n"
        "请为以上每件家具提供价格区间、平价替代方案和总费用估算。"
    )
    analysis = run_agent(price, price_input, "Price-Agent")

    # Step 3: Quote 生成报价单
    quote_input = (
        f"客户需求：{user_query}\n\n家具推荐：\n{rec}\n\n价格分析：\n{analysis}\n\n"
        "请生成一份正式报价单，逐项列出费用。"
    )
    run_agent(quote, quote_input, "Quote-Agent")
    print()


# ═══════════════════════════════════════════════════════════
# 模式 2：并发式 (Concurrent / Fan-out)
#
# qwen-agent 没有内置并发机制，但可以借助 asyncio.gather
# 同时运行多个 Assistant 实例。
#
# 关键：每个 Assistant 是独立的，互不阻塞，
# 结果收集后汇总展示。
# ═══════════════════════════════════════════════════════════

def demo_2_concurrent():
    print("=" * 60)
    print("模式 2：并发式 — Researcher ‖ Planner（asyncio.gather）")
    print("=" * 60)

    researcher = Assistant(llm=llm_cfg, name="Researcher-Agent", system_message=RESEARCHER_INSTRUCTIONS)
    planner = Assistant(llm=llm_cfg, name="Plan-Agent", system_message=PLANNER_INSTRUCTIONS)

    user_query = "Plan a trip to Tokyo in December, interested in technology and food."
    print(f"\n📋 任务分发: {user_query}")
    print("   → Researcher ‖ Planner（并行执行）\n")

    async def run_both():
        return await asyncio.gather(
            run_agent_async(researcher, user_query),
            run_agent_async(planner, user_query),
        )

    research_result, plan_result = asyncio.run(run_both())

    print(f"\n{'='*50}")
    print("📊 汇聚结果")
    print(f"{'='*50}")
    print(f"\n--- Researcher 输出 ---\n{research_result}")
    print(f"\n--- Planner 输出 ---\n{plan_result}")
    print()


# ═══════════════════════════════════════════════════════════
# 模式 3：条件式 (Conditional)
#
# 通过解析 Reviewer 的输出（PASS / REVISE）决定下一步。
# PASS → Publisher 发布
# REVISE → Writer 重写（最多 3 轮）
#
# 和 LangGraph add_conditional_edges 本质上做的事情一样：
# 路由函数 + 循环。
# ═══════════════════════════════════════════════════════════

def demo_3_conditional():
    print("=" * 60)
    print("模式 3：条件式 — Writer → Reviewer → (PASS→Publisher / REVISE→重写)")
    print("=" * 60)

    writer = Assistant(llm=llm_cfg, name="Writer-Agent", system_message=WRITER_INSTRUCTIONS)
    reviewer = Assistant(llm=llm_cfg, name="Reviewer-Agent", system_message=REVIEWER_INSTRUCTIONS)
    publisher = Assistant(llm=llm_cfg, name="Publisher-Agent", system_message=PUBLISHER_INSTRUCTIONS)

    outline = "写一篇关于 AI Agent 中 Tool Calling 机制的入门教程。"

    draft = None
    max_iterations = 3

    for iteration in range(1, max_iterations + 1):
        # Step 1: Write / Revise
        if draft is None:
            prompt = outline
        else:
            prompt = (
                f"你的上一稿被驳回。请修改重写：\n\n"
                f"原稿：\n{draft}\n\n根据大纲重写，确保超过 200 字：\n{outline}"
            )
        draft = run_agent(writer, prompt, f"Writer-Agent (第{iteration}轮)")

        # Step 2: Review
        review = run_agent(reviewer, f"请审核以下稿件是否超过 200 字：\n\n{draft}", "Reviewer-Agent")

        # Step 3: Route
        first_line = review.strip().split("\n")[0].upper()
        if "PASS" in first_line:
            print(f"\n✅ 审核通过（第{iteration}轮），进入发布。")
            run_agent(publisher, f"以下内容已通过审核，请宣布发布并总结要点：\n\n{draft}", "Publisher-Agent")
            break
        else:
            print(f"\n🔄 稿件未通过审核（第{iteration}轮），返回 Writer 重写...")
    else:
        print(f"\n⚠️  已达最大重写次数({max_iterations}轮)，强制发布。")
        run_agent(publisher, f"以下内容请发布（已达最大重写次数）：\n\n{draft}", "Publisher-Agent")
    print()


# ═══════════════════════════════════════════════════════════
# 运行所有示例
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    demo_1_sequential()
    demo_2_concurrent()
    demo_3_conditional()
