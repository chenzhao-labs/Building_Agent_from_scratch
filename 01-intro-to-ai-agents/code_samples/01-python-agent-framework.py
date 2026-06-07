"""
Lesson 01 - AI 代理介绍（通义千问适配版）

用 openai SDK 直连通义千问 API，不依赖任何 Agent 框架。
核心：手动实现 tool calling 循环，理解所有 Agent 框架的底层机制。

运行前：
  1. 设置环境变量 DASHSCOPE_API_KEY=你的千问APIKey
  2. pip install openai python-dotenv
"""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

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


# ── 工具定义 ────────────────────────────────────────────
# 每个工具 = 一个普通 Python 函数 + 一份 JSON Schema
# JSON Schema 告诉 LLM 这个工具叫什么、做什么、需要什么参数

def get_destinations() -> list[str]:
    """获取热门度假目的地列表。"""
    return [
        "巴塞罗那", "巴黎", "柏林", "东京",
        "悉尼", "纽约", "开罗", "开普敦",
        "里约热内卢", "巴厘岛",
    ]


TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_destinations",
            "description": "获取热门度假目的地列表，返回所有可选目的地名称",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]

TOOL_MAP = {
    "get_destinations": get_destinations,
}


# ── 核心：tool calling 循环 ─────────────────────────────
# 这是每一个 Agent 框架底层在做的事：
#   1. 把 (system prompt + 用户消息 + 工具列表) 发给 LLM
#   2. LLM 返回：要么文本（结束），要么 tool_calls（需要执行工具）
#   3. 如果有 tool_calls → 执行对应函数 → 把结果追加到对话 → 回到步骤 1
#   4. 如果返回文本 → 输出给用户

def run_agent(system_prompt: str, user_message: str) -> str:
    """运行 agent，自动处理 tool calling 循环。"""
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

        # 没有 tool_calls → LLM 给出了最终回复
        if not msg.tool_calls:
            return msg.content

        # 有 tool_calls → 执行工具，结果追加到对话，继续循环
        messages.append(_assistant_message(msg))

        for tc in msg.tool_calls:
            func = TOOL_MAP.get(tc.function.name)
            result = func() if func else f"未知工具: {tc.function.name}"
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False),
            })


def run_agent_stream(system_prompt: str, user_message: str):
    """
    流式版本：先处理 tool calls（非流式），最终文本回复用流式输出。
    适合聊天场景，用户能实时看到文字逐字出现。
    """
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
            # 最终文本回复 → 用流式重新请求
            messages.append({"role": "assistant", "content": msg.content})
            stream = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    print(delta.content, end="", flush=True)
            print()
            return

        # 有 tool_calls → 执行工具，继续循环
        messages.append(_assistant_message(msg))
        for tc in msg.tool_calls:
            func = TOOL_MAP.get(tc.function.name)
            result = func() if func else f"未知工具: {tc.function.name}"
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False),
            })


def _assistant_message(msg) -> dict:
    """把 openai SDK 的 message 对象转为 messages 列表可用的 dict。"""
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


# ── 运行示例 ────────────────────────────────────────────

SYSTEM_PROMPT = (
    "你是一个有帮助的旅行代理人。根据用户的偏好，帮助他们找到完美的度假目的地。"
    "使用 get_destinations 工具查看可选目的地列表。"
    "回复时使用中文。"
)

if __name__ == "__main__":
    # 示例 1：普通运行（非流式）
    print("=" * 50)
    print("示例 1：推荐温暖的海滩目的地")
    print("=" * 50)
    result = run_agent(
        SYSTEM_PROMPT,
        "我想找一个温暖的海滩目的地，你有什么推荐？",
    )
    print(result)
    print()

    # 示例 2：流式输出
    print("=" * 50)
    print("示例 2：流式输出 - 介绍东京")
    print("=" * 50)
    run_agent_stream(
        SYSTEM_PROMPT,
        "给我介绍一下东京作为旅游目的地",
    )
