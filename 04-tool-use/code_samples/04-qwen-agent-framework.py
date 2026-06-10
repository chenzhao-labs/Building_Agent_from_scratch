"""
Lesson 04 - 工具使用设计模式（qwen-agent 框架版）

用 qwen-agent 框架实现多工具组合、结构化输出和工具审批模式。

本课核心：
  1. 多工具 — 用 @register_tool 注册多个工具，Assistant 自动管理调用顺序
  2. 结构化输出 — Pydantic + system_message 约束 JSON
  3. 工具审批 — 在 BaseTool.call() 中实现审批逻辑

运行前：
  1. 设置环境变量 DASHSCOPE_API_KEY=你的千问APIKey
  2. pip install -U "qwen-agent[gui]" pydantic
"""

import json
import os

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    raise RuntimeError("请设置环境变量 DASHSCOPE_API_KEY")

llm_cfg = {
    "model": "qwen-flash",
    "model_type": "qwen_dashscope",
    "api_key": api_key,
}


# ═══════════════════════════════════════════════════════════
# 工具定义
# ═══════════════════════════════════════════════════════════

from qwen_agent.tools.base import BaseTool, register_tool


@register_tool("get_destinations")
class GetDestinations(BaseTool):
    description = "获取可用的度假目的地列表"
    parameters = []

    def call(self, params: str, **kwargs) -> str:
        destinations = [
            "巴塞罗那", "巴黎", "柏林", "东京", "悉尼", "纽约"
        ]
        return "\n".join(destinations)


@register_tool("check_availability")
class CheckAvailability(BaseTool):
    description = "检查目的地的预订可用性"
    parameters = [
        {
            "name": "destination",
            "type": "string",
            "description": "要检查的目的地名称",
            "required": True,
        },
    ]

    def call(self, params: str, **kwargs) -> str:
        args = json.loads(params) if isinstance(params, str) else params
        destination = args.get("destination", "")
        availability = {
            "巴塞罗那": "可用 — 剩余 3 个名额",
            "巴黎": "可用",
            "柏林": "已售罄",
            "东京": "可用 — 剩余 1 个名额",
            "悉尼": "可用",
            "纽约": "可用",
        }
        return availability.get(destination, "未知目的地")


@register_tool("get_flight_info")
class GetFlightInfo(BaseTool):
    description = "获取两个城市之间的航班信息"
    parameters = [
        {"name": "origin", "type": "string", "description": "出发机场代码", "required": True},
        {"name": "destination", "type": "string", "description": "目的机场代码", "required": True},
    ]

    def call(self, params: str, **kwargs) -> str:
        args = json.loads(params) if isinstance(params, str) else params
        origin = args.get("origin", "")
        destination = args.get("destination", "")
        flights = {
            "LHR-BCN": "BA 2042, 出发 08:30, 到达 11:45, $350",
            "LHR-CDG": "AF 1081, 出发 09:15, 到达 11:30, $280",
            "LHR-NRT": "JL 044, 出发 11:00, 到达 07:00+1, $890",
        }
        return flights.get(
            f"{origin}-{destination}",
            f"没有从 {origin} 到 {destination} 的直飞航班",
        )


@register_tool("book_flight")
class BookFlight(BaseTool):
    description = "预订航班。这是敏感操作，执行前需要人工审批。"
    parameters = [
        {"name": "origin", "type": "string", "description": "出发机场代码", "required": True},
        {"name": "destination", "type": "string", "description": "目的机场代码", "required": True},
        {"name": "passenger_name", "type": "string", "description": "乘客姓名", "required": True},
    ]

    def call(self, params: str, **kwargs) -> str:
        args = json.loads(params) if isinstance(params, str) else params
        origin = args.get("origin", "")
        destination = args.get("destination", "")
        passenger = args.get("passenger_name", "")

        # 敏感操作：需要人工审批
        print(f"\n⚠️  Agent 想执行敏感操作: book_flight")
        print(f"   参数: origin={origin}, destination={destination}, passenger={passenger}")
        confirm = input("   是否批准执行？(y/n): ").strip().lower()
        if confirm != "y":
            return "操作被用户拒绝。预订未完成。"

        return (
            f"航班已预订：{origin} → {destination}，乘客 {passenger}，"
            f"确认号 #TRV-{hash(passenger) % 10000:04d}"
        )


# ═══════════════════════════════════════════════════════════
# 通用运行函数
# ═══════════════════════════════════════════════════════════

from qwen_agent.agents import Assistant


def run_agent(agent, user_query: str) -> str:
    """运行 agent 一轮，返回 assistant 的最终文本回复。"""
    messages = [{"role": "user", "content": user_query}]
    response_text = ""
    for responses in agent.run(messages=messages):
        if responses:
            last = responses[-1]
            if last.get("role") == "assistant" and last.get("content"):
                response_text = last["content"]
    return response_text


# ═══════════════════════════════════════════════════════════
# 示例 1：多工具组合
#
# 一个 Assistant 同时持有 3 个工具，LLM 自动编排调用顺序。
# 框架内部完成了和原生版一样的 tool calling 循环。
# ═══════════════════════════════════════════════════════════

def demo_1_multi_tool():
    print("=" * 60)
    print("示例 1：多工具组合")
    print("=" * 60)

    agent = Assistant(
        llm=llm_cfg,
        name="TravelToolAgent",
        system_message="你是一个旅行代理。使用可用工具回答关于目的地、可用性和航班的问题。回复时使用中文。",
        function_list=["get_destinations", "check_availability", "get_flight_info"],
    )
    reply = run_agent(agent, "有哪些目的地？哪些还可用？")
    print(reply)
    print()


# ═══════════════════════════════════════════════════════════
# 示例 2：结构化输出
# ═══════════════════════════════════════════════════════════

class BookingRecommendation(BaseModel):
    destination: str
    available: bool
    flight_details: str
    estimated_cost: int


class TravelPlan(BaseModel):
    recommendations: list[BookingRecommendation]


def demo_2_structured_output():
    print("=" * 60)
    print("示例 2：结构化输出")
    print("=" * 60)

    agent = Assistant(
        llm=llm_cfg,
        name="StructuredTravelAgent",
        system_message=(
            "你是一个旅行代理。使用工具查询目的地、可用性和航班信息。"
            "最后以严格的 JSON 格式输出推荐结果：\n"
            '{"recommendations": [{"destination": "...", "available": true/false, '
            '"flight_details": "...", "estimated_cost": 数字}]}'
            "不要包含 markdown 代码块标记。"
        ),
        function_list=["get_destinations", "check_availability", "get_flight_info"],
    )
    raw = run_agent(
        agent,
        "我想从伦敦希思罗飞往欧洲暖和的地方。帮我看看有什么可用的。",
    )

    try:
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        plan = TravelPlan.model_validate_json(raw)
        for r in plan.recommendations:
            status = "✅ 可用" if r.available else "❌ 不可用"
            print(f"  {status} {r.destination} | {r.flight_details} | 约${r.estimated_cost}")
    except Exception as e:
        print(f"[解析失败] {e}")
        print(f"原始回复: {raw[:300]}")
    print()


# ═══════════════════════════════════════════════════════════
# 示例 3：工具审批模式
#
# qwen-agent 没有 MAF 那样的 approval_mode 参数。
# 但可以在 BaseTool.call() 内部实现审批逻辑（input() 拦截）。
# 和在原生版的做法一样。
# ═══════════════════════════════════════════════════════════

def demo_3_approval_mode():
    """演示：在工具内部实现审批。"""
    print("=" * 60)
    print("示例 3：工具审批模式（敏感操作需人工确认）")
    print("=" * 60)

    agent = Assistant(
        llm=llm_cfg,
        name="BookingAgent",
        system_message=(
            "你是一个旅行代理。使用工具帮助用户查询和预订航班。"
            "注意：book_flight 是敏感操作，会触发人工审批。"
            "回复时使用中文。"
        ),
        function_list=["get_flight_info", "book_flight"],
    )
    reply = run_agent(
        agent,
        "帮我预订从 LHR 到 BCN 的航班，乘客姓名 Zhang Wei。",
    )
    print(f"\n最终回复: {reply}")
    print()


# ═══════════════════════════════════════════════════════════
# 运行所有示例
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    demo_1_multi_tool()
    demo_2_structured_output()
    # 示例 3 需要交互输入，默认跳过
    demo_3_approval_mode()
    # print("示例 3（工具审批）需要交互输入，已跳过。")
    # print("取消注释 main 中的 demo_3_approval_mode() 即可运行。")
