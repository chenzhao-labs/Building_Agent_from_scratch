"""
Lesson 03 - Agentic 设计模式（通义千问适配版 · 原生 SDK）

三种构建高效 AI Agent 的基础设计模式：
  模式 1：清晰的 Agent 指令 — 精确的角色、职责、约束定义
  模式 2：结构化输出 — Pydantic 模型确保可预测、可验证的返回
  模式 3：单一职责 Agent — 每个 Agent 只专注做好一件事

场景：旅行目的地推荐系统

运行前：
  1. 设置环境变量 DASHSCOPE_API_KEY=你的千问APIKey
  2. pip install openai python-dotenv pydantic
"""

import json
import os
from typing import Annotated

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
# 共享工具
# ═══════════════════════════════════════════════════════════

def get_destination_details(destination: str) -> str:
    """获取度假目的地的详细信息。"""
    details = {
        "巴塞罗那": "巴塞罗那可用。最佳季节 5-6月。海滩、建筑、夜生活。约$2000/周。",
        "东京": "东京可用。最佳季节 3-4月。文化、美食、科技。约$2500/周。",
        "开普敦": "开普敦不可用。最佳季节 11-3月。自然、红酒、探险。约$1800/周。",
        "巴黎": "巴黎可用。最佳季节 4-6月、9-10月。艺术、美食、时尚。约$2200/周。",
    }
    return details.get(destination, f"{destination}：暂无信息。")


TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_destination_details",
            "description": "获取度假目的地的详细信息，包括可用性、最佳季节、亮点、预算估算。",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {
                        "type": "string",
                        "description": "要查询的目的地名称",
                    },
                },
                "required": ["destination"],
            },
        },
    },
]

TOOL_MAP = {"get_destination_details": get_destination_details}


def _tool_loop(messages: list[dict]) -> str:
    """执行 tool calling 循环，返回 LLM 的最终文本回复。"""
    max_tool_rounds = 5  # 最多5轮工具调用
    tool_call_count = 0
    
    while tool_call_count < max_tool_rounds:
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
            )
            msg = response.choices[0].message
            
            # print(f"[DEBUG] tool_calls: {msg.tool_calls}")
            # print(f"[DEBUG] content: {msg.content[:100] if msg.content else 'None'}")
            
            # 如果没有 tool_calls，返回最终内容
            if not msg.tool_calls:
                final_content = msg.content or "无法生成回复"
                messages.append({"role": "assistant", "content": final_content})
                return final_content
            
            # 有 tool_calls：先添加 assistant 消息
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
            
            # 执行所有 tool calls
            for tc in msg.tool_calls:
                func_name = tc.function.name
                func = TOOL_MAP.get(func_name)
                
                if not func:
                    result = f"错误：未知工具 '{func_name}'"
                else:
                    try:
                        args = json.loads(tc.function.arguments)
                        result = func(**args)
                        # print(f"[DEBUG] Tool {func_name}({args}) -> {result}")
                    except json.JSONDecodeError as e:
                        result = f"错误：解析工具参数失败 - {e}"
                    except Exception as e:
                        result = f"错误：执行工具时出错 - {e}"
                
                # 添加 tool 响应消息
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })
            
            tool_call_count += 1
            
            # 继续循环，让模型处理工具返回结果
            
        except Exception as e:
            error_msg = f"API 调用错误: {e}"
            print(f"[错误] {error_msg}")
            return error_msg
    
    # 达到最大工具调用次数
    final_response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )
    return final_response.choices[0].message.content or "无法生成回复"


# ═══════════════════════════════════════════════════════════
# 模式 1：清晰的 Agent 指令
#
# 好的指令定义：
#   1. Agent 是谁（角色 + 语气）
#   2. Agent 应该做什么（分步骤职责）
#   3. Agent 应该如何表现（约束 + 风格）
# ═══════════════════════════════════════════════════════════

INSTRUCTIONS_TRAVEL_CONCIERGE = """\
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

回复使用中文，保持温暖专业的语气。
"""


def pattern_1_clear_instructions():
    """演示：清晰指令如何塑造 agent 的每次回复。"""
    print("=" * 60)
    print("模式 1：清晰的 Agent 指令")
    print("=" * 60)

    user_query = "我想度一个星期的假，预算$2500，喜欢美食和历史。"
    messages = [
        {"role": "system", "content": INSTRUCTIONS_TRAVEL_CONCIERGE},
        {"role": "user", "content": user_query},
    ]
    print(f"User：{user_query}\n")
    reply = _tool_loop(messages)
    print(f"Assistant：{reply}")
    print()


# ═══════════════════════════════════════════════════════════
# 模式 2：使用 Pydantic 的结构化输出
#
# 自由文本适合对话，但下游系统需要结构化数据。
# 通过 Pydantic 模型定义精确的输出 schema，
# 让 LLM 输出 JSON，然后用 Pydantic 验证和解析。
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


def pattern_2_structured_output():
    """演示：让 LLM 输出结构化 JSON，用 Pydantic 验证。"""
    print("=" * 60)
    print("模式 2：结构化输出（Pydantic）")
    print("=" * 60)

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

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": "推荐3个适合文化旅行者的目的地，预算$2500以内。"},
    ]
    raw = _tool_loop(messages)

    # 用 Pydantic 验证和解析
    try:
        parsed = TravelRecommendations.model_validate_json(raw)
        print(f"个性化备注: {parsed.personalized_note}")
        for r in parsed.recommendations:
            status = "✅ 可用" if r.available else "❌ 不可用"
            print(f"  {status} {r.destination} | 最佳季节: {r.best_season} | 预算: ${r.estimated_budget_usd}")
            print(f"    亮点: {', '.join(r.highlights)}")
    except Exception as e:
        print(f"[解析失败] {e}")
        print(f"原始回复: {raw[:200]}...")
    print()



# ═══════════════════════════════════════════════════════════
# 模式 3：单一职责 Agent
#
# 复杂任务拆分给多个专注的 Agent：
#   - DestinationExpert：只管目的地研究和推荐（有工具）
#   - LogisticsPlanner：只管行程规划（无工具，纯推理）
#
# 这反映了软件工程的"关注点分离"原则。
# ═══════════════════════════════════════════════════════════

DESTINATION_EXPERT_PROMPT = """\
你是一个目的地研究专家。你唯一的工作是：
1. 根据旅行者偏好评估目的地
2. 使用 get_destination_details 工具检查可用性
3. 返回一个简短的排序列表，包含优缺点
不要讨论航班、酒店或后勤——那由另一个 agent 负责。回复使用中文。"""

LOGISTICS_PLANNER_PROMPT = """\
你是一个旅行后勤规划师。你唯一的工作是：
1. 为选定的目的地创建每日行程
2. 在预算范围内建议航班和酒店选项
3. 注明签证要求和旅行保险建议
不要推荐目的地——那由另一个 agent 负责。回复使用中文。"""


def pattern_3_single_responsibility():
    """演示：两个专注的 agent 顺序协作。"""
    print("=" * 60)
    print("模式 3：单一职责 Agent")
    print("=" * 60)

    # Step 1: Destination Expert 选择最佳目的地
    dest_messages = [
        {"role": "system", "content": DESTINATION_EXPERT_PROMPT},
        {"role": "user", "content": "我想度一周的文化美食之旅，预算$2500以内。推荐最好的目的地。"},
    ]
    dest_result = _tool_loop(dest_messages)
    print("=== Destination Expert ===")
    print(dest_result)
    print()

    # Step 2: Logistics Planner 基于第一步的结果做规划
    logistics_messages = [
        {"role": "system", "content": LOGISTICS_PLANNER_PROMPT},
        {"role": "user", "content": f"基于以下推荐，规划一周的旅行：\n{dest_result}"},
    ]
    logistics_result = _tool_loop(logistics_messages)
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