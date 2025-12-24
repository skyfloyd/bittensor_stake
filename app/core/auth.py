from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional, Dict, Any
from .config import get_settings

settings = get_settings()

class AuthManager:
    def __init__(self):
        """Initialize the authentication manager."""
        self.api_key_header = APIKeyHeader(name="Authorization", auto_error=True)
        self.api_token = settings.API_TOKEN

    def verify_token(self, token: str) -> bool:
        """
        Verify if a token is valid.

        Args:
            token (str): The API token

        Returns:
            bool: True if token is valid, False otherwise
        """
        return token == self.api_token

# Create a global instance
auth_manager = AuthManager()