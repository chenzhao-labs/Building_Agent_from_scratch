"""
Lesson 03 - Agentic 设计模式（qwen-agent 框架版）

三种设计模式用 qwen-agent 框架实现，对比原生 SDK 看框架提供的便利：

  模式 1：清晰的 Agent 指令 → Assistant(system_message=...)
  模式 2：结构化输出 → Pydantic + JSON 解析
  模式 3：单一职责 Agent → 多个 Assistant 各司其职，顺序协作

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
# 共享工具
# ═══════════════════════════════════════════════════════════

from qwen_agent.tools.base import BaseTool, register_tool


@register_tool("get_destination_details")
class GetDestinationDetails(BaseTool):
    description = "获取度假目的地的详细信息，包括可用性、最佳季节、亮点、预算估算。"
    parameters = [
        {
            "name": "destination",
            "type": "string",
            "description": "要查询的目的地名称",
            "required": True,
        },
    ]

    def call(self, params: str, **kwargs) -> str:
        args = json.loads(params) if isinstance(params, str) else params
        destination = args.get("destination", "")
        details = {
            "巴塞罗那": "巴塞罗那可用。最佳季节 5-6月。海滩、建筑、夜生活。约$2000/周。",
            "东京": "东京可用。最佳季节 3-4月。文化、美食、科技。约$2500/周。",
            "开普敦": "开普敦不可用。最佳季节 11-3月。自然、红酒、探险。约$1800/周。",
            "巴黎": "巴黎可用。最佳季节 4-6月、9-10月。艺术、美食、时尚。约$2200/周。",
        }
        return details.get(destination, f"{destination}：暂无信息。")


# ═══════════════════════════════════════════════════════════
# 通用运行函数
# ═══════════════════════════════════════════════════════════

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
# 模式 1：清晰的 Agent 指令
#
# system_message 定义三要素：
#   我是谁 + 我该做什么 + 我该怎么做
# 这个 system_message 会伴随每次 LLM 调用，持续塑造 agent 行为。
# ═══════════════════════════════════════════════════════════

from qwen_agent.agents import Assistant


def pattern_1_clear_instructions():
    """演示：清晰指令如何通过 Assistant.system_message 塑造行为。"""
    print("=" * 60)
    print("模式 1：清晰的 Agent 指令")
    print("=" * 60)

    concierge = Assistant(
        llm=llm_cfg,
        name="TravelConcierge",
        system_message="""你是一位名叫 Alex 的奢华旅行礼宾专员。

重要规则：
1. 你必须使用 get_destination_details 工具查询目的地信息
2. 如果查询的目的地不可用（返回"暂无信息"），你应该查询其他目的地
3. 不要凭空编造信息，始终基于工具返回的真实数据做推荐
4. 推荐的流程：先查询2-3个可能的目的地 → 根据返回结果筛选 → 推荐最佳选择

可用目的地：巴黎、东京、巴塞罗那、开普敦

示例：
用户：推荐美食历史目的地
步骤1：查询 get_destination_details("巴黎")
步骤2：查询 get_destination_details("东京")  
步骤3：查询 get_destination_details("巴塞罗那")
步骤4：基于结果推荐

回复使用中文，保持温暖专业的语气。""",
        function_list=["get_destination_details"],
    )
    reply = run_agent(concierge, "我想度一个星期的假，预算$2500，喜欢美食和历史。")
    print(reply)
    print()


# ═══════════════════════════════════════════════════════════
# 模式 2：结构化输出
#
# qwen-agent 的 Assistant 没有直接的 response_format 参数。
# 通过在 system_message 中指定 JSON schema，让 LLM 输出 JSON，
# 然后用 Pydantic 验证解析。这和原生版逻辑一致。
# ═══════════════════════════════════════════════════════════

class DestinationRecommendation(BaseModel):
    destination: str
    available: bool
    best_season: str
    highlights: list[str]
    estimated_budget_usd: int


class TravelRecommendations(BaseModel):
    recommendations: list[DestinationRecommendation]
    personalized_note: str


system = """\
你是一位名叫 Alex 的奢华旅行礼宾专员。

重要规则：
1. 你必须使用 get_destination_details 工具查询目的地信息
2. 如果查询的目的地不可用（返回"暂无信息"），你应该查询其他目的地
3. 不要凭空编造信息，始终基于工具返回的真实数据做推荐
4. 推荐的流程：先查询2-3个可能的目的地 → 根据返回结果筛选 → 推荐最佳选择

可用目的地：巴黎、东京、巴塞罗那、开普敦

示例：
用户：推荐美食历史目的地
步骤1：查询 get_destination_details("巴黎")
步骤2：查询 get_destination_details("东京")  
步骤3：查询 get_destination_details("巴塞罗那")
步骤4：基于结果推荐

最终回复必须是严格的 JSON 格式，不要包含任何其他文字。
输出格式示例：
{
  "recommendations": [
    {
      "destination": "巴黎",
      "available": true,
      "best_season": "4-6月、9-10月",
      "highlights": ["艺术", "美食", "时尚"],
      "estimated_budget_usd": 2200
    }
  ],
  "personalized_note": "根据您的偏好，我推荐..."
}
"""

def pattern_2_structured_output():
    """演示：通过 system_message 约束 JSON 输出 + Pydantic 验证。"""
    print("=" * 60)
    print("模式 2：结构化输出（Pydantic）")
    print("=" * 60)

    structured_agent = Assistant(
        llm=llm_cfg,
        name="StructuredTravelExpert",
        system_message=system,
        function_list=["get_destination_details"],
    )
    raw = run_agent(
        structured_agent,
        "推荐3个适合文化旅行者的目的地，预算$2500以内。",
    )

    try:
        # 尝试从 markdown 代码块中提取 JSON
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        parsed = TravelRecommendations.model_validate_json(raw)
        print(f"个性化备注: {parsed.personalized_note}")
        for r in parsed.recommendations:
            status = "✅ 可用" if r.available else "❌ 不可用"
            print(f"  {status} {r.destination} | 最佳季节: {r.best_season} | 预算: ${r.estimated_budget_usd}")
            print(f"    亮点: {', '.join(r.highlights)}")
    except Exception as e:
        print(f"[解析失败] {e}")
        print(f"原始回复: {raw[:300]}...")
    print()


# ═══════════════════════════════════════════════════════════
# 模式 3：单一职责 Agent
#
# 两个 Assistant，各自独立的 system_message 和工具集。
# 第一个产出推荐 → 第二个基于推荐做规划。
# 和 MAF 版一样，但 qwen-agent 不需要 WorkflowBuilder，
# Python 函数调用就是你的编排层。
# ═══════════════════════════════════════════════════════════

def pattern_3_single_responsibility():
    """演示：两个专注的 Assistant 顺序协作。"""
    print("=" * 60)
    print("模式 3：单一职责 Agent")
    print("=" * 60)

    destination_agent = Assistant(
        llm=llm_cfg,
        name="DestinationExpert",
        system_message="""你是一个目的地研究专家。你唯一的工作是：
1. 根据旅行者偏好评估目的地
2. 使用 get_destination_details 工具检查可用性
3. 返回一个简短的排序列表，包含优缺点
不要讨论航班、酒店或后勤——那由另一个 agent 负责。回复使用中文。""",
        function_list=["get_destination_details"],
    )

    logistics_agent = Assistant(
        llm=llm_cfg,
        name="LogisticsPlanner",
        system_message="""你是一个旅行后勤规划师。你唯一的工作是：
1. 为选定的目的地创建每日行程
2. 在预算范围内建议航班和酒店选项
3. 注明签证要求和旅行保险建议
不要推荐目的地——那由另一个 agent 负责。回复使用中文。""",
    )

    dest_result = run_agent(
        destination_agent,
        "我想度一周的文化美食之旅，预算$2500以内。推荐最好的目的地。",
    )
    print("=== Destination Expert ===")
    print(dest_result)
    print()

    logistics_result = run_agent(
        logistics_agent,
        f"基于以下推荐，规划一周的旅行：\n{dest_result}",
    )
    print("=== Logistics Planner ===")
    print(logistics_result)
    print()


# ═══════════════════════════════════════════════════════════
# 运行所有示例
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    # pattern_1_clear_instructions()
    # pattern_2_structured_output()
    pattern_3_single_responsibility()
