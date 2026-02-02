"""OAuth2 authentication middleware for Databricks Apps."""

import os
import logging
import json
import subprocess
from fastapi import Request, HTTPException
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def get_databricks_cli_token() -> Optional[str]:
    """
    Get authentication token from Databricks CLI for local development.

    Returns:
        OAuth token from Databricks CLI, or None if unavailable
    """
    try:
        databricks_host = os.getenv("DATABRICKS_HOST")
        if not databricks_host:
            logger.warning("DATABRICKS_HOST not set, cannot get CLI token")
            return None

        # Get token from Databricks CLI
        result = subprocess.run(
            ["databricks", "auth", "token", "--host", databricks_host],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            token_data = json.loads(result.stdout)
            access_token = token_data.get("access_token")
            logger.info("Successfully obtained token from Databricks CLI")
            return access_token
        else:
            logger.warning(f"Failed to get CLI token: {result.stderr}")
            return None

    except Exception as e:
        logger.warning(f"Error getting CLI token: {e}")
        return None


async def get_current_user(request: Request) -> Dict:
    """
    Extract user OAuth token from Databricks Apps request headers.

    In Databricks Apps (production), the user's OAuth token is automatically
    injected in the x-forwarded-access-token header by the Databricks gateway.
    The token is already validated by the gateway, so we just need to
    extract it and decode the user identity.

    In local development, if the header is not present, we try to get a token
    from the Databricks CLI to authenticate as the local user.

    Args:
        request: FastAPI request object

    Returns:
        Dict with user_id and token

    Raises:
        HTTPException: If token is missing and cannot be obtained from CLI
    """
    # Extract token from x-forwarded-access-token header (production)
    user_token = request.headers.get('x-forwarded-access-token')

    # If no token in headers, try to get from Databricks CLI (local development)
    if not user_token:
        logger.info("No token in headers, attempting to get from Databricks CLI")
        user_token = get_databricks_cli_token()

        if not user_token:
            logger.error("No authentication token available")
            raise HTTPException(
                status_code=401,
                detail="No user authentication token found. For local development, ensure Databricks CLI is configured."
            )

    # Decode JWT to extract user_id (token already validated by Databricks gateway or CLI)
    user_id = extract_user_id_from_token(user_token)

    logger.info(f"Authenticated user: {user_id}")

    return {
        "user_id": user_id,
        "token": user_token
    }


def extract_user_id_from_token(token: str) -> str:
    """
    Decode JWT token to extract user email/id.

    The token is already validated by the Databricks gateway,
    so we only need to decode it to extract user identity.
    No signature verification is required.

    Args:
        token: OAuth2 JWT token

    Returns:
        User email or ID
    """
    try:
        import jwt
        # No signature verification - already validated by Databricks gateway
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get("email") or payload.get("sub") or "unknown_user"
        logger.debug(f"Extracted user_id from token: {user_id}")
        return user_id
    except Exception as e:
        logger.warning(f"Failed to decode JWT token: {e}, using fallback user_id")
        return "databricks_user"  # Fallback
