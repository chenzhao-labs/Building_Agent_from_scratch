"""
Lesson 01 - AI 代理介绍（qwen-agent 框架版）

使用 qwen-agent 框架调用通义千问 API，对比理解 Agent 框架的抽象层次。

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

# ── LLM 配置 ────────────────────────────────────────────

llm_cfg = {
    "model": "qwen-flash",
    "model_type": "qwen_dashscope",
    "api_key": api_key,
}

# ── 工具定义 ────────────────────────────────────────────
# qwen-agent 提供两种定义工具的方式：
#   A：@register_tool 装饰普通函数
#   B：继承 BaseTool 类（需要复杂参数校验时用）

from qwen_agent.tools.base import BaseTool, register_tool


@register_tool("get_destinations")
class GetDestinations(BaseTool):
    description = "获取热门度假目的地列表，返回所有可选目的地名称"
    parameters = []

    def call(self, params: str, **kwargs) -> str:
        destinations = [
            "巴塞罗那", "巴黎", "柏林", "东京",
            "悉尼", "纽约", "开罗", "开普敦",
            "里约热内卢", "巴厘岛",
        ]
        return "\n".join(destinations)


# ── 创建 Agent ──────────────────────────────────────────
# Assistant 是 qwen-agent 的通用 Agent 类，等价于原版的 provider.create_agent()

from qwen_agent.agents import Assistant

agent = Assistant(
    llm=llm_cfg,
    name="TravelAgent",
    system_message=(
        "你是一个有帮助的旅行代理人。根据用户的偏好，帮助他们找到完美的度假目的地。"
        "使用 get_destinations 工具查看可选目的地列表。"
        "回复时使用中文。"
    ),
    function_list=["get_destinations"],
)


# ── 运行 Agent ──────────────────────────────────────────
# agent.run() 是生成器，每次 yield 一条完整的对话轮次消息列表。
# 和原版 agent.run() 的行为类似，但接口是生成器模式。

def run_once(user_query: str):
    """运行一次对话，返回完整回复文本。"""
    messages = [{"role": "user", "content": user_query}]
    response_text = ""
    for responses in agent.run(messages=messages):
        # responses 是这一轮的完整消息列表，取最后一条 assistant 回复
        if responses:
            last = responses[-1]
            if last.get("role") == "assistant" and last.get("content"):
                response_text = last["content"]
    return response_text


def run_stream(user_query: str):
    """流式运行：逐轮输出 assistant 的回复内容。"""
    messages = [{"role": "user", "content": user_query}]
    prev_len = 0
    for responses in agent.run(messages=messages):
        if responses:
            last = responses[-1]
            if last.get("role") == "assistant" and last.get("content"):
                # 只输出增量部分，模拟流式效果
                new_text = last["content"][prev_len:]
                if new_text:
                    print(new_text, end="", flush=True)
                prev_len = len(last["content"])
    print()


# ── 运行示例 ────────────────────────────────────────────

if __name__ == "__main__":
    # 示例 1：普通运行
    print("=" * 50)
    print("示例 1：推荐温暖的海滩目的地")
    print("=" * 50)
    result = run_once("我想找一个温暖的海滩目的地，你有什么推荐？")
    print(result)
    print()

    # 示例 2：流式输出
    print("=" * 50)
    print("示例 2：流式输出 - 介绍东京")
    print("=" * 50)
    run_stream("给我介绍一下东京作为旅游目的地")
