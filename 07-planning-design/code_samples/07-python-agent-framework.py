"""
Lesson 07 - 规划设计模式（通义千问适配版 · 原生 openai SDK）

用 openai SDK 直连通义千问 API，手动实现 tool calling 循环。
演示：1) 结构化输出（Pydantic 模型驱动任务分解）
      2) 规划-执行分离（Planning Agent → Concierge Agent）

核心模式：
  - Planning Agent：将复杂请求分解为结构化的子任务列表（TravelPlan）
  - Concierge Agent：按依赖顺序执行子任务，调用专业工具

运行前：
  1. 设置环境变量 DASHSCOPE_API_KEY=你的千问APIKey
  2. pip install openai python-dotenv pydantic
"""

import json
import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, ValidationError

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


# ── Pydantic 结构化输出模型 ─────────────────────────────

class TravelSubTask(BaseModel):
    task_id: int
    description: str
    assigned_agent: str  # "flight_agent", "hotel_agent", "activity_agent"
    priority: str  # "high", "medium", "low"
    dependencies: list[int] = []


class TravelPlan(BaseModel):
    destination: str
    trip_duration_days: int
    subtasks: list[TravelSubTask]
    total_estimated_budget_usd: int
    notes: str


# ── 规划阶段：结构化输出 ─────────────────────────────────
# qwen-flash 支持 response_format={"type": "json_object"}，
# 通过 system prompt 指定 JSON schema 来实现结构化输出。

PLAN_SCHEMA_DESC = """{
  "destination": "string",
  "trip_duration_days": integer,
  "subtasks": [
    {
      "task_id": integer,
      "description": "string",
      "assigned_agent": "flight_agent | hotel_agent | activity_agent",
      "priority": "high | medium | low",
      "dependencies": [integer]
    }
  ],
  "total_estimated_budget_usd": integer,
  "notes": "string"
}"""


def create_travel_plan(user_request: str) -> TravelPlan:
    """规划 Agent：将旅行请求分解为结构化的 TravelPlan。"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一个旅行规划代理。当收到旅行请求时：\n"
                    "1. 把它分成具体的小任务（航班、酒店、活动、后勤）\n"
                    "2. 把每个子任务分配给合适的专业代理\n"
                    "3. 确定优先事项并找出任务之间的依赖关系\n"
                    "4. 估算总预算\n\n"
                    f"输出必须是符合此模式的有效 JSON：\n{PLAN_SCHEMA_DESC}\n"
                    "只回复 JSON 对象，不要其他文字."
                ),
            },
            {"role": "user", "content": user_request},
        ],
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content
    try:
        return TravelPlan.model_validate_json(raw)
    except ValidationError:
        # 容错：如果 JSON 解析失败，打印原始输出并重新抛出
        print(f"[Warning] Pydantic 校验失败，原始输出:\n{raw}")
        raise


# ── 执行阶段：Concierge Agent 的工具 ────────────────────

def book_flight(destination: str, departure_date: str, return_date: str) -> str:
    """预订航班。"""
    return (
        f"Flight booked to {destination}: {departure_date} → {return_date}, "
        f"confirmation #FLT-{abs(hash(destination)) % 10000:04d}"
    )


def reserve_hotel(city: str, check_in: str, check_out: str, guests: int) -> str:
    """预订酒店。"""
    return (
        f"Hotel reserved in {city}: {check_in} to {check_out} "
        f"for {guests} guests, confirmation #HTL-{abs(hash(city)) % 10000:04d}"
    )


def book_activity(activity_name: str, date: str, participants: int) -> str:
    """预订活动/门票。"""
    return (
        f"Activity booked: {activity_name} on {date} "
        f"for {participants} people, confirmation #ACT-{abs(hash(activity_name)) % 10000:04d}"
    )


TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "book_flight",
            "description": "搜索并预订航班",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string", "description": "目的地城市"},
                    "departure_date": {"type": "string", "description": "出发日期 (YYYY-MM-DD)"},
                    "return_date": {"type": "string", "description": "返回日期 (YYYY-MM-DD)"},
                },
                "required": ["destination", "departure_date", "return_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reserve_hotel",
            "description": "在目的城市预订酒店",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "酒店所在城市"},
                    "check_in": {"type": "string", "description": "入住日期 (YYYY-MM-DD)"},
                    "check_out": {"type": "string", "description": "退房日期 (YYYY-MM-DD)"},
                    "guests": {"type": "integer", "description": "住客人数"},
                },
                "required": ["city", "check_in", "check_out", "guests"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_activity",
            "description": "预订旅游活动、博物馆门票或其他体验项目",
            "parameters": {
                "type": "object",
                "properties": {
                    "activity_name": {"type": "string", "description": "活动或导览名称"},
                    "date": {"type": "string", "description": "活动日期 (YYYY-MM-DD)"},
                    "participants": {"type": "integer", "description": "参与人数"},
                },
                "required": ["activity_name", "date", "participants"],
            },
        },
    },
]

TOOL_MAP = {
    "book_flight": book_flight,
    "reserve_hotel": reserve_hotel,
    "book_activity": book_activity,
}


# ── Tool Calling 循环 ───────────────────────────────────

def _assistant_message(msg) -> dict:
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
            for tc in (msg.tool_calls or [])
        ],
    }


def run_concierge(system_prompt: str, user_message: str) -> str:
    """运行 Concierge Agent，自动处理 tool calling 循环。"""
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

        print(f"  [执行工具] {[tc.function.name for tc in msg.tool_calls]}")
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
    user_request = (
        "为一对对艺术、美食和历史感兴趣的情侣制定一个七天的巴黎旅行计划。"
        "Budget around $5000."
    )

    # ─── 步骤 1：规划 ───
    print("=" * 60)
    print("步骤 1：Planning Agent — 将请求分解为结构化任务")
    print("=" * 60)
    plan = create_travel_plan(user_request)
    print(f"Destination: {plan.destination}")
    print(f"Duration: {plan.trip_duration_days} days")
    print(f"Budget: ${plan.total_estimated_budget_usd}")
    print(f"Notes: {plan.notes}")
    print(f"\nSubtasks ({len(plan.subtasks)}):")
    for task in plan.subtasks:
        deps = f" (deps: {task.dependencies})" if task.dependencies else ""
        print(f"  [{task.priority.upper():6s}] #{task.task_id} {task.description}")
        print(f"            → {task.assigned_agent}{deps}")
    print()

    # ─── 步骤 2：执行 ───
    print("=" * 60)
    print("步骤 2：Concierge Agent — 按计划执行子任务")
    print("=" * 60)

    subtask_lines = "\n".join(
        f"- [{t.priority}] #{t.task_id}. {t.description} "
        f"(agent: {t.assigned_agent}, deps: {t.dependencies})"
        for t in plan.subtasks
    )
    execution_prompt = (
        f"执行以下前往 {plan.destination} 的旅行计划 "
        f"({plan.trip_duration_days} days, ${plan.total_estimated_budget_usd} budget):\n"
        f"{subtask_lines}\n\n"
        "按顺序完成子任务，注意依赖关系。 "
        "使用现有工具完成每个子任务。 "
        "完成后总结结果。用中文回复。"
    )

    result = run_concierge(
        system_prompt=(
            "你是一个旅行助手，正在执行一个有条理的旅行计划。 "
            "使用可用的工具完成每个子任务。逐步完成这些子任务 "
            "按顺序，尊重依赖关系。完成后总结结果。"
        ),
        user_message=execution_prompt,
    )
    print(result)
