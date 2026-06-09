"""
Lesson 02 - 探索 Agent 框架（通义千问适配版 · 原生 SDK）

用 openai SDK 直连通义千问 API，手写 Agent 框架的四层抽象。
理解所有 Agent 框架（MAF、LangChain、qwen-agent）底层在做什么。

框架四层：
  Client → Agent → Tools → Session
  连接     封装     能力     记忆

运行前：
  1. 设置环境变量 DASHSCOPE_API_KEY=你的千问APIKey
  2. pip install openai python-dotenv
"""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ═══════════════════════════════════════════════════════════
# 第一层：Client — 与 AI 模型的连接
# 对应 MAF 的 AzureAIProjectAgentProvider
# ═══════════════════════════════════════════════════════════

api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    raise RuntimeError("请设置环境变量 DASHSCOPE_API_KEY（https://bailian.console.aliyun.com/）")

client = OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
MODEL = "qwen-flash"


# ═══════════════════════════════════════════════════════════
# 第二层：Tools — 代理可调用的函数
# 对应 MAF 的 @tool 装饰器
# ═══════════════════════════════════════════════════════════

def check_destination_availability(destination: str) -> str:
    """检查度假目的地是否可预订。"""
    available = {
        "巴塞罗那": True,
        "东京": True,
        "开罗": False,
        "里约热内卢": True,
        "巴黎": False,
    }
    is_available = available.get(destination, False)
    return f"{destination} is {'available' if is_available else 'not available'} for booking."


TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "check_destination_availability",
            "description": "检查度假目的地是否可预订。",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {
                        "type": "string",
                        "description": "要检查可用性的目的地名称",
                    },
                },
                "required": ["destination"],
            },
        },
    },
]

TOOL_MAP = {
    "check_destination_availability": check_destination_availability,
}


# ═══════════════════════════════════════════════════════════
# 第三层：Agent — Client + Instructions + Tools 的封装
# 对应 MAF 的 provider.create_agent(name, instructions, tools)
# ═══════════════════════════════════════════════════════════

SYSTEM_PROMPT = (
    "你是一个旅行预订代理。帮助用户检查目的地可用性并给出推荐。"
    "在推荐目的地之前，务必先检查其可用性。"
    "回复时使用中文。"
)


def _assistant_message(msg) -> dict:
    """将 openai SDK message 对象转为 messages 列表可用的 dict。"""
    if not msg.tool_calls:
        return {"role": "assistant", "content": msg.content}
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
            for tc in msg.tool_calls
        ],
    }


def _execute_tools(msg) -> list[dict]:
    """执行 LLM 请求的所有 tool_calls，返回 tool 消息列表。"""
    results = []
    for tc in msg.tool_calls:
        func = TOOL_MAP.get(tc.function.name)
        if func:
            args = json.loads(tc.function.arguments)
            result = func(**args)
        else:
            result = f"未知工具: {tc.function.name}"
        results.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": result,
        })
    return results


# ═══════════════════════════════════════════════════════════
# 第四层：Session — 多轮对话的记忆
# 对应 MAF 的 agent.create_session()
#
# 核心：一个 messages 列表在多次 run() 调用之间保持引用。
# 每次调用把新消息追加到同一个列表里，Agent 就有了"记忆"。
# ═══════════════════════════════════════════════════════════

def run_agent(user_message: str, messages: list[dict]) -> str:
    """
    运行一次 agent 对话轮次。

    参数：
      user_message: 本轮用户输入
      messages:     对话历史列表（充当 session，需要外部保持引用）

    返回 agent 的文本回复。
    调用后 messages 会包含本轮的 user/assistant/tool 消息。
    """
    messages.append({"role": "user", "content": user_message})

    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS_SCHEMA,
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            messages.append({"role": "assistant", "content": msg.content})
            return msg.content

        messages.append(_assistant_message(msg))
        messages.extend(_execute_tools(msg))


# ═══════════════════════════════════════════════════════════
# 运行示例：多轮对话，展示 session 记忆
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    # 创建 session（就是一个带 system prompt 的 messages 列表）
    session = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("=" * 60)
    print("第 1 轮：询问可用目的地")
    print("=" * 60)
    reply = run_agent("我想去巴黎，是否可以预定？", session)
    print(reply)
    print()

    print("=" * 60)
    print("第 2 轮：追问（agent 记得上一轮说了什么）")
    print("=" * 60)
    reply = run_agent("我想去暖和的地方。推荐目的地？", session)
    print(reply)
    print()

    # 验证 session 里有多少条消息
    print(f"[Session 中共有 {len(session)} 条消息]")
    # print(session)
