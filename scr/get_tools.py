from langchain_mcp_adapters.client import MultiServerMCPClient

_MCP_CONFIG = {
    "search_tools": {
        "transport": "http",
        "url": "http://mcp_search_server:8080/mcp",  # MCP HTTP endpoint
    }
}


async def get_all_tools():
    """Recieving all tools"""
    try:
        mcp_client = MultiServerMCPClient(_MCP_CONFIG)
        mcp_tools = await mcp_client.get_tools()
        print(f"Get {len(mcp_tools)} instruments")
        return mcp_tools
    except Exception as e:
        print(f"No MCP")


async def get_query_refine_instructions() -> str:
    """Fetch the refine_query prompt from the MCP server and return its text content.

    The returned text is intended to be appended to the agent's system prompt
    so the LLM knows how to formulate optimal search queries.

    Returns:
        Prompt text string, or empty string if the server is unavailable.
    """
    try:
        mcp_client = MultiServerMCPClient(_MCP_CONFIG)
        async with mcp_client.session("search_tools") as session:
            result = await session.get_prompt(
                "refine_query", arguments={"query": ""}
            )
            # result.messages is a list of PromptMessage objects.
            # Each message has a .content attribute with a .text field.
            texts = [
                msg.content.text
                for msg in result.messages
                if hasattr(msg.content, "text")
            ]
            return "\n".join(texts)
    except Exception as e:
        print(f"Could not fetch refine_query prompt from MCP server: {e}")
        return ""
