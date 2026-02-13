"""
实践基地标签分类Agent
用于对实践基地进行三级标签分类：省份、主题、《概论》章节
"""

import os
import json
import sys
from typing import Annotated
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from coze_coding_utils.runtime_ctx.context import default_headers, new_context
from langchain.tools import tool, ToolRuntime

# 导入工具
sys.path.append(os.path.join(os.path.dirname(__file__), '../tools'))
from tools.base_info_search_tool import search_base_info, search_province, search_xi_visited

LLM_CONFIG = "config/agent_llm_config.json"

# 默认保留最近 20 轮对话 (40 条消息)
MAX_MESSAGES = 40

def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]  # type: ignore

class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]

def build_agent():
    """构建Agent"""
    workspace_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(workspace_path, LLM_CONFIG)

    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")

    llm = ChatOpenAI(
        model=cfg['config'].get("model"),
        api_key=api_key,
        base_url=base_url,
        temperature=cfg['config'].get('temperature', 0.7),
        streaming=True,
        timeout=cfg['config'].get('timeout', 600),
        extra_body={
            "thinking": {
                "type": cfg['config'].get('thinking', 'disabled')
            }
        },
        default_headers=default_headers()
    )

    # 构建工具列表
    tools = [search_base_info, search_province, search_xi_visited]

    return create_agent(
        model=llm,
        system_prompt=cfg.get("sp"),
        tools=tools,
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )

def get_memory_saver():
    """获取记忆保存器"""
    try:
        from storage.memory.memory_saver import get_memory_saver as _get_memory_saver
        return _get_memory_saver()
    except ImportError:
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()
