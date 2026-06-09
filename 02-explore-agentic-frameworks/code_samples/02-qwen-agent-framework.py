"""
Lesson 02 - 探索 Agent 框架（qwen-agent 框架版）

用 qwen-agent 框架对比原生 SDK，体会框架替你做了哪些事。
本课核心：理解 Agent 框架的四层抽象在 qwen-agent 中怎么体现。

四层对照：
  MAF                      →  qwen-agent
  ─────────────────────────────────────────────
  AzureAIProjectAgent      →  llm_cfg (DashScope)
  @tool                    →  @register_tool + BaseTool
  create_agent(name,...)   →  Assistant(llm=..., name=..., system_message=..., function_list=[...])
  create_session()         →  messages 列表（手动维护多轮历史）

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

# ═══════════════════════════════════════════════════════════
# 第一层：Client — LLM 连接配置
# 对应 MAF 的 AzureAIProjectAgentProvider
# qwen-agent 用 llm_cfg 字典配置，不需要显式的 provider
# ═══════════════════════════════════════════════════════════

llm_cfg = {
    "model": "qwen-flash",
    "model_type": "qwen_dashscope",
    "api_key": api_key,
}

# ═══════════════════════════════════════════════════════════
# 第二层：Tools — 代理可调用的函数
# 对应 MAF 的 @tool 装饰器
# qwen-agent 提供两种方式：
#   A. @register_tool + 继承 BaseTool（推荐，自动生成 schema）
#   B. 直接注册普通函数
# ═══════════════════════════════════════════════════════════

from qwen_agent.tools.base import BaseTool, register_tool


@register_tool("check_destination_availability")
class CheckDestinationAvailability(BaseTool):
    description = "检查度假目的地是否可预订。"
    parameters = [
        {
            "name": "destination",
            "type": "string",
            "description": "要检查可用性的目的地名称",
            "required": True,
        },
    ]

    def call(self, params: str, **kwargs) -> str:
        import json

        args = json.loads(params) if isinstance(params, str) else params
        destination = args.get("destination", "")
        available = {
            "巴塞罗那": True,
            "东京": True,
            "开罗": False,
            "里约热内卢": True,
            "巴黎": False,
        }
        is_available = available.get(destination, False)
        state = "可预订" if is_available else "不可预订"
        return f"{destination} 当前{state}。"


# ═══════════════════════════════════════════════════════════
# 第三层：Agent — Client + Instructions + Tools 的封装
# 对应 MAF 的 provider.create_agent(name, instructions, tools)
# ═══════════════════════════════════════════════════════════

from qwen_agent.agents import Assistant

agent = Assistant(
    llm=llm_cfg,
    name="TravelAvailabilityAgent",
    system_message=(
        "你是一个旅行预订代理。帮助用户检查目的地可用性并给出推荐。"
        "在推荐目的地之前，务必先检查其可用性。"
        "回复时使用中文。"
    ),
    function_list=["check_destination_availability"],
)


# ═══════════════════════════════════════════════════════════
# 第四层：Session — 多轮对话的记忆
# 对应 MAF 的 agent.create_session() + agent.run(..., session=session)
#
# qwen-agent 没有显式的 session 对象。
# 多轮记忆通过手动维护 messages 列表实现：
#   每次 agent.run(messages) 返回后，把输出消息保留，
#   下一轮把新的 user 消息追加进去即可。
# ═══════════════════════════════════════════════════════════

def run_turn(user_query: str, messages: list[dict]) -> str:
    """
    运行一轮对话，保留上下文到 messages 中。

    参数：
      user_query: 本轮用户输入
      messages:   对话历史（充当 session，外部保持引用）

    返回 agent 的文本回复。
    调用后 messages 会包含本轮的全部更新。
    """
    messages.append({"role": "user", "content": user_query})
    response_text = ""
    new_messages = []
    for responses in agent.run(messages=messages):
        new_messages = responses
        if responses:
            last = responses[-1]
            if last.get("role") == "assistant" and last.get("content"):
                response_text = last["content"]
    # 用 agent 返回的完整消息列表替换，保持历史一致
    messages.clear()
    messages.extend(new_messages)
    return response_text


# ═══════════════════════════════════════════════════════════
# 运行示例：多轮对话，展示 session 记忆
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    # session 就是一个 messages 列表
    session = []

    print("=" * 60)
    print("第 1 轮：询问可用目的地")
    print("=" * 60)
    reply = run_turn("我想去巴黎，是否可以预定？", session)
    print(reply)
    print()

    print("=" * 60)
    print("第 2 轮：追问（agent 记得上一轮说了什么）")
    print("=" * 60)
    reply = run_turn("我想去暖和的地方。有哪些可用的？", session)
    print(reply)
    print()

    print(f"[Session 中共有 {len(session)} 条消息]")
