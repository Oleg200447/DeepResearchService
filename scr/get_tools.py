from langchain_mcp_adapters.client import MultiServerMCPClient


async def get_all_tools():
    """Recieving all tools"""
    try:
        mcp_client = MultiServerMCPClient({
            "search_tools": {
            "transport": "http",
            "url": "http://mcp_search_server:8080/mcp",  # MCP HTTP endpoint
            }
        })
        mcp_tools = await mcp_client.get_tools()
        print(f"Get {len(mcp_tools)} instruments")
        return mcp_tools
    except Exception as e:
        print(f"No MCP")
