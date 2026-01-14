# Deep Research Agent API

REST API service for LangGraph-based agent with per-user session management. Each user maintains their own conversation context using JWT-based authentication.

## Features

- ✅ **Per-User Sessions**: Each user gets isolated conversation context via JWT user ID
- ✅ **JWT Authentication**: Extracts user data from JWT tokens (no validation required)
- ✅ **LangGraph Integration**: Uses InMemorySaver for session persistence
- ✅ **MCP Tools**: Integrates with external MCP servers for extended capabilities
- ✅ **Structured Logging**: JSON-formatted logs with user context
- ✅ **Docker Support**: Multi-stage Dockerfile for production deployment
- ✅ **CORS Enabled**: Configurable cross-origin resource sharing
- ✅ **Health Checks**: Built-in health monitoring endpoint

## Architecture

```
Client Request (JWT + Question)
         ↓
    FastAPI Endpoint
         ↓
    JWT Extraction (user_id from sub field)
         ↓
    LangGraph Agent (thread_id = user_id)
         ↓
    InMemorySaver (session persistence)
         ↓
    Response to Client
```

## Installation

### Local Development

1. **Clone and navigate to project**
   ```bash
   cd DeepResearchClient
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and settings
   ```

5. **Run the service**
   ```bash
   python -m scr.main
   # Or use uvicorn directly:
   uvicorn scr.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Docker Deployment

1. **Build image**
   ```bash
   docker build -t deep-research-agent .
   ```

2. **Run container**
   ```bash
   docker run -d \
     --name deep-research-agent \
     -p 8000:8000 \
     --env-file .env \
     deep-research-agent
   ```

3. **Using Docker Compose**
   ```bash
   docker-compose up -d
   ```

## Configuration

All configuration is done via environment variables. See `.env.example` for available options.

### Required Variables

- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`: At least one LLM API key must be provided

### Optional Variables

- `LLM_MODEL`: Model name (default: gpt-4)
- `LLM_TEMPERATURE`: Model temperature (default: 0.7)
- `MCP_SEARCH_SERVER_URL`: MCP server endpoint
- `SERVICE_PORT`: Service port (default: 8000)
- `LOG_LEVEL`: Logging level (default: INFO)

## API Endpoints

### POST /api/v1/chat

Main chat endpoint for interacting with the agent.

**Request:**
```json
POST /api/v1/chat
Headers:
  Authorization: Bearer <jwt_token>
  Content-Type: application/json

Body:
{
  "question": "What is the weather today?"
}
```

**Response:**
```json
{
  "response": "Agent's response here...",
  "session_id": "user_12345"
}
```

**Error Responses:**
- `401 Unauthorized`: Missing or invalid JWT token
- `400 Bad Request`: Invalid request body
- `500 Internal Server Error`: Processing error

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

## JWT Token Format

The service expects JWT tokens with the following payload structure:

```json
{
  "sub": "user_12345",      // User ID (used as thread_id)
  "nickname": "john_doe",   // User nickname
  "role": "user",           // User role
  "iss": "auth_service",    // Issuer
  "exp": 1234567890         // Expiration timestamp
}
```

**Note:** The gateway handles JWT validation. This service only extracts the data.

## Session Management

- Each user's `sub` (user_id) from JWT becomes their `thread_id` in LangGraph
- Sessions persist in memory using `InMemorySaver()`
- Multiple requests from the same user maintain conversation context
- Different users have completely isolated sessions

## Logging

Logs are output in JSON format with the following structure:

```json
{
  "timestamp": "2026-01-14T02:49:00.000Z",
  "level": "INFO",
  "logger": "scr.main",
  "message": "Processing chat request",
  "user_id": "user_12345",
  "request_id": "uuid-here"
}
```

## Development

### Project Structure

```
DeepResearchClient/
├── scr/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # FastAPI application
│   ├── agent.py             # LangGraph agent setup
│   ├── auth.py              # JWT extraction
│   ├── config.py            # Configuration management
│   ├── models.py            # Pydantic models
│   ├── logger.py            # Logging setup
│   └── get_tools.py         # MCP tools integration
├── .env.example             # Environment template
├── .gitignore              # Git ignore rules
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose config
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

### Adding New Features

1. **New API Endpoint**: Add to `scr/main.py`
2. **New Models**: Add to `scr/models.py`
3. **Agent Configuration**: Modify `scr/agent.py`
4. **Environment Variables**: Update `scr/config.py` and `.env.example`

## Troubleshooting

### Common Issues

**Service won't start:**
- Check that at least one LLM API key is set
- Verify all required environment variables are present
- Check logs for specific error messages

**JWT extraction fails:**
- Ensure Authorization header format: `Bearer <token>`
- Verify JWT has all required fields (sub, nickname, role, iss, exp)

**Agent not responding:**
- Check MCP server connectivity
- Verify LLM API key is valid
- Review logs for timeout or API errors

## License

[Add your license here]

## Support

[Add support contact information]
