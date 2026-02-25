"""LangGraph agent configuration and initialization."""
from typing import Optional, Any
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from scr.get_tools import get_all_tools
from scr.config import settings
from scr.logger import setup_logger

logger = setup_logger(__name__)


async def create_agent_f():
    """Create and configure LangGraph agent with tools and checkpointer.
    
    Returns:
        Compiled LangGraph agent with InMemorySaver checkpointer
        
    Raises:
        ValueError: If LLM configuration is invalid
    """
    logger.info("Initializing LangGraph agent")
    
    # Validate LLM configuration
    settings.validate_llm_config()
    
    # Initialize LLM based on available API keys
    if settings.use_openrouter and settings.openrouter_api_key:
        logger.info(f"Using OpenRouter with model: {settings.llm_model}")
        llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            # default_headers={
            #     "HTTP-Referer": "http://localhost:8000",
            #     "X-Title": "DeepResearch Agent"
            # }
        )
    elif settings.openai_api_key:
        logger.info(f"Using OpenAI model: {settings.llm_model}")
        llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            api_key=settings.openai_api_key,
        )
    elif settings.anthropic_api_key:
        logger.info(f"Using Anthropic model: {settings.llm_model}")
        llm = ChatAnthropic(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            api_key=settings.anthropic_api_key,
        )
    else:
        raise ValueError("No LLM API key configured")
    
    # Get all tools (MCP tools)
    logger.info("Loading tools")
    tools = await get_all_tools()
    logger.info(f"Loaded {len(tools)} tools")
    
    # Create checkpointer for session persistence
    checkpointer = InMemorySaver()
    logger.info("Initialized InMemorySaver for session persistence")


    system_prompt =    ''' 
                           You are a helpful assistant. You must answer the user's requests using the information found using the search tool.
                           You can only search in the indices that the user has provided to you. If you dont find any info for the your request,
                           you can try to reformulate(maybe exchange it for synonyms, or rich it by object properties, that user try to find) it and try again.
                       '''
    # Create agent with checkpointer
    agent = create_agent(
        model=llm,
        tools=tools,
        checkpointer=checkpointer,
        system_prompt=system_prompt
    )
    
    logger.info("Agent successfully created")
    return agent


# Global agent instance (initialized on startup)
_agent: Optional[Any] = None


async def get_agent():
    """Get or create the global agent instance.
    
    Returns:
        LangGraph agent instance
    """
    global _agent
    if _agent is None:
        _agent = await create_agent_f()
    return _agent
