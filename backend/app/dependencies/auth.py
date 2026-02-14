"""Authentication dependencies."""

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import settings

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Verify the API key for import service.

    Args:
        api_key: The API key from header.

    Returns:
        The validated API key.

    Raises:
        HTTPException: If key is missing or invalid.
    """
    expected_key = settings.import_api_key
    if not expected_key:
        # If not configured, reject all requests for safety
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Import API authentication is not configured on the server",
        )

    if api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    return api_key
