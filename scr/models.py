"""Data models for API requests and responses."""
from pydantic import BaseModel, Field


class JWTData(BaseModel):
    """JWT token data extracted from Authorization header."""
    sub: str  # user_id
    nickname: str
    role: str  # "user" or "system"
    iss: str
    exp: int


class ChatRequest(BaseModel):
    """Chat request from client."""
    question: str = Field(..., min_length=1, description="User question or command")


class ChatResponse(BaseModel):
    """Chat response to client."""
    response: str = Field(..., description="Agent response")
    session_id: str = Field(..., description="User session ID")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(default="healthy")
    version: str = Field(default="1.0.0")
