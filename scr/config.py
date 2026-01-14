"""Configuration management from environment variables."""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # LLM Configuration
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    use_openrouter: bool = False
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.7
    
    # MCP Server Configuration
    mcp_search_server_url: str = "http://mcp_search_server:5005"
    
    # Service Configuration
    service_port: int = 8000
    service_host: str = "0.0.0.0"
    log_level: str = "INFO"
    
    # CORS Configuration
    cors_origins: str = "*"
    cors_allow_credentials: bool = True
    cors_allow_methods: str = "*"
    cors_allow_headers: str = "*"
    
    # Agent Configuration
    max_iterations: int = 15
    agent_timeout: int = 300  # seconds
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    def validate_llm_config(self) -> None:
        """Validate that at least one LLM API key is provided."""
        if not self.openai_api_key and not self.anthropic_api_key and not self.openrouter_api_key:
            raise ValueError(
                "At least one LLM API key must be provided: "
                "OPENAI_API_KEY, ANTHROPIC_API_KEY, or OPENROUTER_API_KEY"
            )


# Global settings instance
settings = Settings()
