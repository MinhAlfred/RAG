"""API Key Authentication - Security middleware for RAG API"""

from typing import Optional
from fastapi import Header, HTTPException, status
from config.settings import settings


async def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """
    Verify API key from X-API-Key header

    Args:
        x_api_key: API key from request header

    Raises:
        HTTPException: If API key is missing or invalid

    Returns:
        str: Validated API key
    """
    # If no API key is configured in settings, skip authentication
    if not settings.RAG_API_KEY:
        return None  # API key authentication disabled

    # Check if API key is provided in request
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key. Please provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Verify API key matches configured key
    if x_api_key != settings.RAG_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )

    return x_api_key
