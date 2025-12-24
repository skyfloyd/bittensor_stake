from fastapi import Request, HTTPException, status
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from .auth import auth_manager

api_key_header = APIKeyHeader(name="Authorization", auto_error=True)

class TokenVerificationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip token verification for certain paths
        if request.url.path in ["/docs", "/openapi.json", "/token", "/"]:
            return await call_next(request)

        try:
            # Get the Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Authorization header is missing"},
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Check if the token is in the correct format
            if not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid token format. Use 'Bearer <token>'"},
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Extract the token
            token = auth_header.split(" ")[1]

            # Verify the token
            if not auth_manager.verify_token(token):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid token"},
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Continue with the request if token is valid
            response = await call_next(request)
            return response

        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token"},
                headers={"WWW-Authenticate": "Bearer"},
            ) 