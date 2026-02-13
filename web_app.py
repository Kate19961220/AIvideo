"""
实践基地标签分类Web应用
简化版，一键运行即可使用
"""

import os
import sys
import json
import streamlit as st
from typing import Annotated
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage
from coze_coding_utils.runtime_ctx.context import default_headers

# 添加工具路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../tools'))
from tools.base_info_search_tool import search_base_info, search_province, search_xi_visited

# 配置
LLM_CONFIG = "config/agent_llm_config.json"
MAX_MESSAGES = 40

def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]

class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]

def get_memory_saver():
    """获取记忆保存器"""
    try:
        from storage.memory.memory_saver import get_memory_saver as _get_memory_saver
        return _get_memory_saver()
    except ImportError:
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()

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

    tools = [search_base_info, search_province, search_xi_visited]

    return create_agent(
        model=llm,
        system_prompt=cfg.get("sp"),
        tools=tools,
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )

# Streamlit 页面配置
st.set_page_config(
    page_title="实践基地标签分类系统",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏛️ 实践基地标签分类系统")
st.markdown("---")

# 侧边栏说明
with st.sidebar:
    st.header("📖 使用说明")
    st.info("""
    **这个系统可以帮助您：**
    
    1. 输入实践基地名称
    2. 自动查询所在省份
    3. 判断习近平总书记是否到访
    4. 匹配相关主题
    5. 对应《概论》章节
    
    **支持的主题包括：**
    - 攀高攻坚、大国重器、绿水青山
    - 健康中国、中华文脉、乡土中国
    - 红色记忆、脱贫攻坚乡村振兴
    - 科学精神、工业文化、美丽中国
    - 以及更多...
    """)

    st.header("⚙️ 系统状态")
    if 'agent' not in st.session_state:
        with st.spinner("正在初始化系统..."):
            try:
                st.session_state.agent = build_agent()
                st.success("✅ 系统已就绪")
            except Exception as e:
                st.error(f"❌ 系统初始化失败: {str(e)}")
    else:
        st.success("✅ 系统运行中")

    st.header("🔄 清除历史")
    if st.button("清除对话历史"):
        if 'messages' in st.session_state:
            st.session_state.messages = []
        st.rerun()

# 主界面
if 'messages' not in st.session_state:
    st.session_state.messages = []

# 显示历史消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 用户输入
if user_input := st.chat_input("请输入实践基地名称，例如：湖南十八洞村"):
    # 显示用户消息
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 生成回复
    with st.chat_message("assistant"):
        with st.spinner("正在分析中，请稍候..."):
            try:
                agent = st.session_state.agent
                config = {"configurable": {"thread_id": "default"}}

                response = agent.invoke(
                    {"messages": [HumanMessage(content=user_input)]},
                    config
                )

                # 提取最终回复
                if response["messages"]:
                    final_message = response["messages"][-1]
                    assistant_response = final_message.content

                    st.markdown(assistant_response)

                    # 保存到历史
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_response
                    })

            except Exception as e:
                error_message = f"处理时出错：{str(e)}"
                st.error(error_message)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message
                })

# 页脚
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 12px;'>
    实践基地标签分类系统 | 支持三级标签体系自动分类
</div>
""", unsafe_allow_html=True)
