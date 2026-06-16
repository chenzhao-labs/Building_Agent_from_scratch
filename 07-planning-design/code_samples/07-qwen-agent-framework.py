"""
Lesson 07 - 规划设计模式（qwen-agent 框架版）

使用 qwen-agent 框架调用通义千问 API。
演示：1) 结构化输出（Pydantic 模型驱动任务分解）
      2) 规划-执行分离（Planning Agent → Concierge Agent）

运行前：
  1. 设置环境变量 DASHSCOPE_API_KEY=你的千问APIKey
  2. pip install -U "qwen-agent[gui]" pydantic
"""

import json
import os

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

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

# ── Pydantic 结构化输出模型 ─────────────────────────────

class TravelSubTask(BaseModel):
    task_id: int
    description: str
    assigned_agent: str
    priority: str
    dependencies: list[int] = []


class TravelPlan(BaseModel):
    destination: str
    trip_duration_days: int
    subtasks: list[TravelSubTask]
    total_estimated_budget_usd: int
    notes: str


# ── 执行阶段工具 ────────────────────────────────────────

from qwen_agent.tools.base import BaseTool, register_tool


@register_tool("book_flight")
class BookFlight(BaseTool):
    description = "搜索并预订航班"
    parameters = [
        {"name": "destination", "type": "string", "description": "目的地城市", "required": True},
        {"name": "departure_date", "type": "string", "description": "出发日期 (YYYY-MM-DD)", "required": True},
        {"name": "return_date", "type": "string", "description": "返回日期 (YYYY-MM-DD)", "required": True},
    ]

    def call(self, params: str, **kwargs) -> str:
        args = json.loads(params) if isinstance(params, str) else params
        return (
            f"Flight booked to {args['destination']}: "
            f"{args['departure_date']} → {args['return_date']}, "
            f"confirmation #FLT-{abs(hash(args['destination'])) % 10000:04d}"
        )


@register_tool("reserve_hotel")
class ReserveHotel(BaseTool):
    description = "在目的城市预订酒店"
    parameters = [
        {"name": "city", "type": "string", "description": "酒店所在城市", "required": True},
        {"name": "check_in", "type": "string", "description": "入住日期 (YYYY-MM-DD)", "required": True},
        {"name": "check_out", "type": "string", "description": "退房日期 (YYYY-MM-DD)", "required": True},
        {"name": "guests", "type": "integer", "description": "住客人数", "required": True},
    ]

    def call(self, params: str, **kwargs) -> str:
        args = json.loads(params) if isinstance(params, str) else params
        return (
            f"Hotel reserved in {args['city']}: {args['check_in']} to {args['check_out']} "
            f"for {args['guests']} guests, confirmation #HTL-{abs(hash(args['city'])) % 10000:04d}"
        )


@register_tool("book_activity")
class BookActivity(BaseTool):
    description = "预订旅游活动、博物馆门票或其他体验项目"
    parameters = [
        {"name": "activity_name", "type": "string", "description": "活动或导览名称", "required": True},
        {"name": "date", "type": "string", "description": "活动日期 (YYYY-MM-DD)", "required": True},
        {"name": "participants", "type": "integer", "description": "参与人数", "required": True},
    ]

    def call(self, params: str, **kwargs) -> str:
        args = json.loads(params) if isinstance(params, str) else params
        return (
            f"Activity booked: {args['activity_name']} on {args['date']} "
            f"for {args['participants']} people, "
            f"confirmation #ACT-{abs(hash(args['activity_name'])) % 10000:04d}"
        )


# ── Agent 运行辅助 ──────────────────────────────────────

from qwen_agent.agents import Assistant

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


def create_travel_plan(user_request: str) -> TravelPlan:
    """规划 Agent：将旅行请求分解为结构化的 TravelPlan。"""
    planner = Assistant(
        llm=llm_cfg,
        name="TravelPlanner",
        system_message=(
            "你是一个旅行规划代理。当收到旅行请求时：\n"
            "1. 把它分成具体的小任务（航班、酒店、活动、后勤）\n"
            "2. 把每个子任务分配给合适的专业代理\n"
            "3. 确定优先事项并找出任务之间的依赖关系\n"
            "4. 估算总预算\n\n"
            f"输出必须是符合此模式的有效 JSON：\n{PLAN_SCHEMA_DESC}\n"
            "只回复 JSON 对象，不要其他文字."
        ),
        function_list=[],
    )
    raw = run_once(planner, user_request)

    # 尝试提取 JSON（容错：LLM 可能用 ```json ... ``` 包裹）
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

    try:
        return TravelPlan.model_validate_json(raw)
    except ValidationError:
        print(f"[Warning] Pydantic 校验失败，原始输出:\n{raw}")
        raise


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

    concierge = Assistant(
        llm=llm_cfg,
        name="Concierge",
        system_message=(
            "你是一个旅行助手，正在执行一个有条理的旅行计划。 "
            "使用可用的工具完成每个子任务。逐步完成这些子任务 "
            "按顺序，尊重依赖关系。完成后总结结果。"
        ),
        function_list=["book_flight", "reserve_hotel", "book_activity"],
    )
    result = run_once(concierge, execution_prompt)
    print(result)
