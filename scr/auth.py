"""JWT authentication and extraction."""
import base64
import json
from typing import Optional
from fastapi import Header, HTTPException, status
from scr.models import JWTData
from scr.logger import setup_logger

logger = setup_logger(__name__)


def decode_jwt_payload(token: str) -> dict:
    """Decode JWT token payload without validation.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload as dictionary
        
    Raises:
        ValueError: If token format is invalid
    """
    try:
        # JWT format: header.payload.signature
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")
        
        # Decode payload (second part)
        payload = parts[1]
        
        # Add padding if needed
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += "=" * padding
        
        # Decode base64
        decoded = base64.urlsafe_b64decode(payload)
        
        # Parse JSON
        payload_data = json.loads(decoded)
        
        return payload_data
        
    except Exception as e:
        logger.error(f"Failed to decode JWT: {e}")
        raise ValueError(f"Failed to decode JWT token: {str(e)}")


async def get_jwt_data(authorization: Optional[str] = Header(None)) -> JWTData:
    """Extract and parse JWT data from Authorization header.
    
    Args:
        authorization: Authorization header value (Bearer <token>)
        
    Returns:
        Parsed JWT data
        
    Raises:
        HTTPException: If authorization header is missing or invalid
    """
    if not authorization:
        logger.warning("Missing Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header"
        )
    
    # Check Bearer scheme
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning(f"Invalid Authorization header format: {authorization}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected: Bearer <token>"
        )
    
    token = parts[1]
    
    try:
        # Decode JWT payload
        payload = decode_jwt_payload(token)
        
        # Parse into JWTData model
        jwt_data = JWTData(**payload)
        
        logger.info(f"Successfully extracted JWT data for user: {jwt_data.sub}")
        
        return jwt_data
        
    except ValueError as e:
        logger.error(f"Failed to decode JWT: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid JWT token format"
        )
    except Exception as e:
        logger.error(f"Failed to parse JWT data: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid JWT token data"
        )
