"""
Lesson 04 - 工具使用设计模式（通义千问适配版 · 原生 SDK）

本课涵盖：
  1. 多工具定义 — 用 JSON Schema 描述工具，用 Python 函数实现
  2. 多工具组合 — 一个 agent 同时持有多个工具，LLM 自主选择调用哪个
  3. 结构化输出 — Pydantic 模型 + LLM 输出 JSON，下游代码可靠消费
  4. 工具审批模式 — 敏感操作（如预订）需要人工确认后才能执行

场景：旅行预订代理（可查询目的地、检查可用性、获取航班、预订机票）

运行前：
  1. 设置环境变量 DASHSCOPE_API_KEY=你的千问APIKey
  2. pip install openai python-dotenv pydantic
"""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    raise RuntimeError("请设置环境变量 DASHSCOPE_API_KEY（https://bailian.console.aliyun.com/）")

client = OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
MODEL = "qwen-flash"


# ═══════════════════════════════════════════════════════════
# 工具定义
# ═══════════════════════════════════════════════════════════

def get_destinations() -> list[str]:
    """获取可用的度假目的地列表。"""
    return ["巴塞罗那", "巴黎", "柏林", "东京", "悉尼", "纽约"]


def check_availability(destination: str) -> str:
    """检查目的地的预订可用性。"""
    availability = {
        "爱尔兰": "可用 — 剩余 3 个名额",
        "巴黎": "可用",
        "柏林": "已售罄",
        "东京": "可用 — 剩余 1 个名额",
        "悉尼": "可用",
        "纽约": "可用",
    }
    return availability.get(destination, "未知目的地")


def get_flight_info(origin: str, destination: str) -> str:
    """获取两个城市之间的航班信息。"""
    flights = {
        "LHR-BCN": "BA 2042, 出发 08:30, 到达 11:45, $350",
        "LHR-CDG": "AF 1081, 出发 09:15, 到达 11:30, $280",
        "LHR-NRT": "JL 044, 出发 11:00, 到达 07:00+1, $890",
    }
    return flights.get(
        f"{origin}-{destination}",
        f"没有从 {origin} 到 {destination} 的直飞航班",
    )


# ═══════════════════════════════════════════════════════════
# 工具 Schema（JSON Schema 格式，告诉 LLM 有什么工具、什么参数）
# ═══════════════════════════════════════════════════════════

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_destinations",
            "description": "获取可用的度假目的地列表",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "检查目的地的预订可用性",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {
                        "type": "string",
                        "description": "要检查的目的地名称",
                    },
                },
                "required": ["destination"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_flight_info",
            "description": "获取两个城市之间的航班信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "出发机场代码"},
                    "destination": {"type": "string", "description": "目的机场代码"},
                },
                "required": ["origin", "destination"],
            },
        },
    },
]

TOOL_MAP = {
    "get_destinations": lambda **kwargs: json.dumps(get_destinations(), ensure_ascii=False),
    "check_availability": lambda **kwargs: check_availability(**kwargs),
    "get_flight_info": lambda **kwargs: get_flight_info(**kwargs),
}


def _tool_loop(messages: list[dict], tools_schema: list[dict] = None) -> str:
    """执行 tool calling 循环，返回 LLM 的最终文本回复。"""
    if tools_schema is None:
        tools_schema = TOOLS_SCHEMA
    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools_schema,
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            messages.append({"role": "assistant", "content": msg.content})
            return msg.content

        messages.append({
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
        })
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


# ═══════════════════════════════════════════════════════════
# 示例 1：多工具组合
#
# Agent 同时持有三个工具（get_destinations、check_availability、
# get_flight_info），LLM 自动决定先调哪个、后调哪个、传什么参数。
# ═══════════════════════════════════════════════════════════

def demo_1_multi_tool():
    print("=" * 60)
    print("示例 1：多工具组合")
    print("=" * 60)

    messages = [
        {
            "role": "system",
            "content": "你是一个旅行代理。使用可用工具回答关于目的地、可用性和航班的问题。"
                       "回复时使用中文。",
        },
        {"role": "user", "content": "有哪些目的地？哪些还可用？"},
    ]
    reply = _tool_loop(messages)
    print(reply)
    print()


# ═══════════════════════════════════════════════════════════
# 示例 2：结构化输出
#
# 通过 Pydantic 模型定义输出格式，让 LLM 输出 JSON，
# 然后用 Pydantic 验证。下游代码不再需要解析自由文本。
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

    messages = [
        {
            "role": "system",
            "content": (
                "你是一个旅行代理。使用工具查询目的地、可用性和航班信息。"
                "最后以严格的 JSON 格式输出推荐结果：\n"
                '{"recommendations": [{"destination": "...", "available": true/false, '
                '"flight_details": "...", "estimated_cost": 数字}]}'
                "不要包含 markdown 代码块标记。回复使用中文。"
            ),
        },
        {
            "role": "user",
            "content": "我想从伦敦希思罗飞往欧洲暖和的地方。帮我看看有什么可用的。",
        },
    ]
    raw = _tool_loop(messages)

    # Pydantic 验证
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
# 对于有副作用的操作（预订、扣款），需要人工确认。
# 在原生 SDK 中，我们通过敏感工具标记 + 执行前拦截来实现。
# ═══════════════════════════════════════════════════════════

# 敏感工具：需要人工审批
SENSITIVE_TOOLS = {"book_flight"}


def book_flight(origin: str, destination: str, passenger_name: str) -> str:
    """预订航班（敏感操作，需人工审批）。"""
    return (
        f"航班已预订：{origin} → {destination}，乘客 {passenger_name}，"
        f"确认号 #TRV-{hash(passenger_name) % 10000:04d}"
    )


# 扩展的 tool map（包含敏感工具）
EXTENDED_TOOL_MAP = {
    **TOOL_MAP,
    "book_flight": lambda **kwargs: book_flight(**kwargs),
}

EXTENDED_TOOLS_SCHEMA = TOOLS_SCHEMA + [
    {
        "type": "function",
        "function": {
            "name": "book_flight",
            "description": "预订航班。这是敏感操作，执行前需要人工审批。",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "出发机场代码"},
                    "destination": {"type": "string", "description": "目的机场代码"},
                    "passenger_name": {"type": "string", "description": "乘客姓名"},
                },
                "required": ["origin", "destination", "passenger_name"],
            },
        },
    },
]


def _tool_loop_with_approval(messages: list[dict]) -> str:
    """带审批拦截的 tool calling 循环。"""
    while True:
        # 只传非敏感工具给 LLM（让 LLM 知道 book_flight 存在但不主动调）
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=EXTENDED_TOOLS_SCHEMA,
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            messages.append({"role": "assistant", "content": msg.content})
            return msg.content

        messages.append({
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
        })

        for tc in msg.tool_calls:
            func_name = tc.function.name
            args = json.loads(tc.function.arguments)

            # 敏感工具：需要人工审批
            if func_name in SENSITIVE_TOOLS:
                print(f"\n⚠️  Agent 想执行敏感操作: {func_name}")
                print(f"   参数: {json.dumps(args, ensure_ascii=False)}")
                confirm = input("   是否批准执行？(y/n): ").strip().lower()
                if confirm != "y":
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": "操作被用户拒绝。请告知用户预订未完成，需要批准。",
                    })
                    continue

            func = EXTENDED_TOOL_MAP.get(func_name)
            result = func(**args) if func else f"未知工具: {func_name}"
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })


def demo_3_approval_mode():
    """演示：工具审批模式。"""
    print("=" * 60)
    print("示例 3：工具审批模式（敏感操作需人工确认）")
    print("=" * 60)

    messages = [
        {
            "role": "system",
            "content": (
                "你是一个旅行代理。使用工具帮助用户查询和预订航班。"
                "注意：book_flight 是敏感操作，会触发人工审批。"
                "回复时使用中文。"
            ),
        },
        {
            "role": "user",
            "content": "帮我预订从 LHR 到 BCN 的航班，乘客姓名 Zhang Wei。",
        },
    ]
    reply = _tool_loop_with_approval(messages)
    print(f"\n最终回复: {reply}")
    print()


# ═══════════════════════════════════════════════════════════
# 运行所有示例
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    demo_1_multi_tool()
    demo_2_structured_output()
    # 示例 3 需要交互输入，默认跳过。取消注释即可运行：
    # demo_3_approval_mode()
    print("示例 3（工具审批）需要交互输入，已跳过。")
    print("取消注释 main 中的 demo_3_approval_mode() 即可运行。")
