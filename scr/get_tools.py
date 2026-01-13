from langgraph_mcp import MultiServerMCPClient


async def get_all_tools():
    """Получение всех инструментов: MCP + управление сессией."""

    try:
        mcp_client = MultiServerMCPClient({
            "search_tools": {
            "transport": "http",
            "url": "http://mcp_search_server:5005",  # MCP HTTP endpoint
            }
        })
        mcp_tools = await mcp_client.get_tools()
        print(f"Подключено {len(mcp_tools)} инструментов filesystem")
        return mcp_tools
    except Exception as e:
        print(f"MCP недоступен, используем базовые инструменты")
