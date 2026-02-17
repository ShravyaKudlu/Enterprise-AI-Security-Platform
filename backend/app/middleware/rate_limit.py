from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limits on API endpoints."""

    def __init__(self, app):
        super().__init__(app)
        self.request_counts = {}  # Simple in-memory store

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health check
        if request.url.path == "/health":
            return await call_next(request)

        client_ip = get_remote_address(request)
        endpoint = request.url.path

        # Define rate limits per endpoint
        limits = {
            "/api/v1/security-tests/run": (10, 3600),  # 10 per hour
            "/api/v1/variants/generate": (50, 3600),  # 50 per hour
        }

        # Default limit for other endpoints
        default_limit = (1000, 3600)  # 1000 per hour
        limit_count, limit_period = limits.get(endpoint, default_limit)

        # Check rate limit (simplified implementation)
        key = f"{client_ip}:{endpoint}"

        # For production, use Redis-based rate limiting
        # This is a simplified version

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit_count)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit_count - 1))

        return response
