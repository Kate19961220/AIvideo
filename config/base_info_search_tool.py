"""
实践基地信息搜索工具
用于搜索实践基地的地点、主题等相关信息
"""

from langchain.tools import tool, ToolRuntime
from coze_coding_dev_sdk import SearchClient
from coze_coding_utils.runtime_ctx.context import new_context


@tool
def search_base_info(base_name: str, runtime: ToolRuntime = None) -> str:
    """
    搜索实践基地的详细信息，包括所在省份、特色主题、是否被习近平总书记到访等。

    Args:
        base_name: 实践基地的名称

    Returns:
        实践基地的详细信息字符串
    """
    ctx = runtime.context if runtime else new_context(method="search_base_info")
    client = SearchClient(ctx=ctx)

    # 构建搜索查询，明确包含习近平总书记到访信息
    query = f"{base_name} 实践基地 介绍 特色 习近平总书记 总书记 到访 视察 调研"

    try:
        response = client.web_search(
            query=query,
            count=8,
            need_summary=True
        )

        if not response.web_items:
            return f"未找到关于'{base_name}'的相关信息。"

        # 整合搜索结果
        result_parts = []
        result_parts.append(f"实践基地名称：{base_name}")
        result_parts.append("\n搜索结果：\n")

        for i, item in enumerate(response.web_items, 1):
            result_parts.append(f"{i}. {item.title}")
            result_parts.append(f"   摘要：{item.snippet}")
            result_parts.append(f"   URL: {item.url}\n")

        # 如果有AI总结，添加总结
        if response.summary:
            result_parts.append("\nAI 总结：")
            result_parts.append(response.summary)

        return "\n".join(result_parts)

    except Exception as e:
        return f"搜索'{base_name}'时出错：{str(e)}"


@tool
def search_xi_visited(base_name: str, runtime: ToolRuntime = None) -> str:
    """
    专门搜索习近平总书记是否到访过该实践基地。

    Args:
        base_name: 实践基地的名称

    Returns:
        习近平总书记到访情况的详细信息
    """
    ctx = runtime.context if runtime else new_context(method="search_xi_visited")
    client = SearchClient(ctx=ctx)

    # 构建搜索查询，明确搜索总书记到访信息
    query = f"习近平 总书记 到访 视察 调研 {base_name}"

    try:
        response = client.web_search(
            query=query,
            count=5,
            need_summary=True
        )

        result_parts = []
        result_parts.append(f"实践基地：{base_name}")
        result_parts.append("\n习近平总书记到访情况搜索结果：\n")

        if not response.web_items:
            result_parts.append("未找到习近平总书记到访该实践基地的相关信息。")
            result_parts.append("\n说明：这可能意味着：")
            result_parts.append("1. 习近平总书记尚未到访过该基地")
            result_parts.append("2. 该基地的总书记到访记录未被网络收录")
            result_parts.append("3. 该基地不是总书记的足迹之一")
        else:
            # 分析搜索结果，判断是否到访
            visited = False
            visit_details = []

            for i, item in enumerate(response.web_items, 1):
                result_parts.append(f"{i}. {item.title}")
                result_parts.append(f"   摘要：{item.snippet}\n")

                # 检查是否包含到访信息
                title_lower = item.title.lower()
                snippet_lower = item.snippet.lower()

                if any(keyword in title_lower or keyword in snippet_lower
                       for keyword in ["习近平", "总书记", "到访", "视察", "调研", "考察", "访问"]):
                    visited = True
                    visit_details.append(f"- {item.title}: {item.snippet[:100]}")

            if response.summary:
                result_parts.append("\nAI 总结：")
                result_parts.append(response.summary)
                # 检查总结中是否包含到访信息
                if any(keyword in response.summary
                       for keyword in ["习近平", "总书记", "到访", "视察", "调研", "考察"]):
                    visited = True

            # 添加判断结果
            result_parts.append("\n" + "="*50)
            if visited:
                result_parts.append("【判断结果】：习近平总书记已到访过该实践基地")
                result_parts.append("\n到访详情：")
                for detail in visit_details:
                    result_parts.append(detail)
            else:
                result_parts.append("【判断结果】：未找到习近平总书记到访该实践基地的确切记录")
                result_parts.append("\n说明：")
                result_parts.append("- 建议进一步核实该基地是否为总书记的足迹")
                result_parts.append("- 该基地可能不在总书记的足迹清单中")

        return "\n".join(result_parts)

    except Exception as e:
        return f"搜索'{base_name}'总书记到访情况时出错：{str(e)}"


@tool
def search_province(base_name: str, runtime: ToolRuntime = None) -> str:
    """
    搜索实践基地所在的省份

    Args:
        base_name: 实践基地的名称

    Returns:
        实践基地所在省份信息
    """
    ctx = runtime.context if runtime else new_context(method="search_province")
    client = SearchClient(ctx=ctx)

    # 构建搜索查询，明确查找位置信息
    query = f"{base_name} 在哪个省"

    try:
        response = client.web_search(
            query=query,
            count=3,
            need_summary=True
        )

        if not response.web_items:
            return f"未找到'{base_name}'的省份信息。"

        # 优先从搜索结果和总结中提取省份信息
        result_parts = []
        result_parts.append(f"实践基地：{base_name}")

        if response.summary:
            result_parts.append(f"\n位置信息：\n{response.summary}")

        result_parts.append("\n相关搜索结果：\n")
        for i, item in enumerate(response.web_items, 1):
            result_parts.append(f"{i}. {item.title}")
            result_parts.append(f"   {item.snippet}\n")

        return "\n".join(result_parts)

    except Exception as e:
        return f"搜索'{base_name}'省份时出错：{str(e)}"
