"""FastAPI application for LangGraph agent service."""
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain_core.messages import HumanMessage, AIMessage

from scr.models import ChatRequest, ChatResponse, HealthResponse, JWTData
from scr.auth import get_jwt_data
from scr.agent import get_agent
from scr.config import settings
from scr.logger import setup_logger, log_with_context

logger = setup_logger(__name__, level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting application")
    
    # Initialize agent on startup
    try:
        await get_agent()
        logger.info("Agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}", exc_info=True)
        raise
    
    yield
    
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title="Deep Research Agent API",
    description="REST API for LangGraph-based agent with per-user sessions",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods.split(",") if settings.cors_allow_methods != "*" else ["*"],
    allow_headers=settings.cors_allow_headers.split(",") if settings.cors_allow_headers != "*" else ["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """Global exception handler for uncaught exceptions."""
    request_id = str(uuid.uuid4())
    logger.error(
        f"Unhandled exception: {exc}",
        extra={"request_id": request_id},
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "request_id": request_id
        }
    )


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint.
    
    Returns:
        Service health status
    """
    return HealthResponse()


@app.post("/api/v1/chat", response_model=ChatResponse, tags=["Agent"])
async def chat(
    request: ChatRequest,
    jwt_data: JWTData = Depends(get_jwt_data),
):
    """Process user question and return agent response.
    
    Args:
        request: Chat request with user question
        jwt_data: JWT data extracted from Authorization header
        
    Returns:
        Agent response with session ID
        
    Raises:
        HTTPException: If processing fails
    """
    request_id = str(uuid.uuid4())
    user_id = jwt_data.sub
    logger.info(f"{request.topics}")
    log_with_context(
        logger,
        "info",
        f"Processing chat request",
        user_id=user_id,
        request_id=request_id,
        topics = request.topics[0],
        question=request.question[:100]  # Log first 100 chars
    )
    
    try:
        # Get agent instance
        agent = await get_agent()
        
        # Create configuration with user-specific thread_id
        config = {
            "configurable": {
                "thread_id": user_id
            }
        }
        
        log_with_context(
            logger,
            "debug",
            f"Using thread_id: {user_id}",
            user_id=user_id,
            request_id=request_id
        )
        
        # Create user message with topics
        topics_str = f"Indices: {', '.join(request.topics)}. " if request.topics else ""
        user_message = HumanMessage(content=f"{topics_str}{request.question}")
        
        # Stream agent response
        response_content = ""
        async for chunk in agent.astream(
            {"messages": [user_message]},
            config=config,
            stream_mode="values"
        ):
            if "messages" in chunk and chunk["messages"]:
                last_msg = chunk["messages"][-1]
                
                if isinstance(last_msg, AIMessage) and last_msg.content:
                    response_content = last_msg.content
        
        if not response_content:
            log_with_context(
                logger,
                "warning",
                "Agent returned empty response",
                user_id=user_id,
                request_id=request_id
            )
            response_content = "I apologize, but I couldn't generate a response. Please try again."
        
        log_with_context(
            logger,
            "info",
            f"Successfully processed request",
            user_id=user_id,
            request_id=request_id,
            response_length=len(response_content)
        )
        
        return ChatResponse(
            response=response_content,
            session_id=user_id
        )
        
    except Exception as e:
        log_with_context(
            logger,
            "error",
            f"Error processing chat request: {e}",
            user_id=user_id,
            request_id=request_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process request"
        )


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.service_host}:{settings.service_port}")
    uvicorn.run(
        "scr.main:app",
        host=settings.service_host,
        port=settings.service_port,
        reload=False,
        log_level=settings.log_level.lower()
    )
