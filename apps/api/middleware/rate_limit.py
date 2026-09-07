# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/middleware/rate_limit.py"
# purpose: "Production sliding window rate limiting middleware with Redis and in-memory resilience for DDoS/brute-force protection."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import os
import time
from typing import Dict, List, Optional, Tuple
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from scripts.security.rate_limiter import RateLimiter, RateLimitResult
except ImportError:
    RateLimiter = None
    RateLimitResult = None


class InMemorySlidingWindowLimiter:
    """In-memory sliding window rate limiter fallback when Redis is unavailable."""

    def __init__(self):
        self._store: Dict[str, List[float]] = {}

    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> Tuple[bool, int, float]:
        now = time.time()
        window_start = now - window_seconds

        timestamps = self._store.get(key, [])
        # Prune expired timestamps
        valid_timestamps = [t for t in timestamps if t > window_start]

        if len(valid_timestamps) >= max_requests:
            oldest = valid_timestamps[0]
            reset_at = oldest + window_seconds
            self._store[key] = valid_timestamps
            return False, 0, reset_at

        valid_timestamps.append(now)
        self._store[key] = valid_timestamps
        remaining = max_requests - len(valid_timestamps)
        reset_at = now + window_seconds
        return True, remaining, reset_at


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Production-grade rate limiting middleware.
    Protects API endpoints with sliding-window rate limits,
    with sensitive route tiering and Redis/in-memory failover.
    """

    BYPASS_PATHS = {
        "/health",
        "/api/health",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico",
    }

    SENSITIVE_PREFIXES = (
        "/auth",
        "/api/auth",
        "/checkout",
        "/api/checkout",
        "/webhooks",
        "/api/webhooks",
    )

    def __init__(
        self,
        app,
        redis_url: Optional[str] = None,
        default_limit: int = 100,
        sensitive_limit: int = 20,
        window_seconds: int = 60,
    ):
        super().__init__(app)
        self.default_limit = default_limit
        self.sensitive_limit = sensitive_limit
        self.window_seconds = window_seconds
        self.in_memory_limiter = InMemorySlidingWindowLimiter()

        self.redis_limiter = None
        if redis_url and RateLimiter is not None:
            try:
                self.redis_limiter = RateLimiter(redis_url=redis_url)
                # Quick ping to verify connectivity
                self.redis_limiter.redis.ping()
            except Exception:
                self.redis_limiter = None

    def _get_client_identifier(self, request: Request) -> str:
        # Check forwarded headers first for reverse proxies
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        client = request.client
        return client.host if client else "unknown_client"

    def _get_limits_for_path(self, path: str) -> Tuple[int, int]:
        for prefix in self.SENSITIVE_PREFIXES:
            if path.startswith(prefix):
                return self.sensitive_limit, self.window_seconds
        return self.default_limit, self.window_seconds

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # 1. Bypass check: testing environment or health probes
        is_testing = bool(os.getenv("TESTING") == "1" or os.getenv("PYTEST_CURRENT_TEST"))
        if is_testing or path in self.BYPASS_PATHS:
            return await call_next(request)

        client_ip = self._get_client_identifier(request)
        max_requests, window_seconds = self._get_limits_for_path(path)
        limiter_key = f"rate_limit:{client_ip}:{path.split('/')[1] if len(path.split('/')) > 1 else 'root'}"

        allowed = True
        remaining = max_requests
        reset_at = time.time() + window_seconds

        # 2. Try Redis rate limiter if active
        if self.redis_limiter:
            try:
                res = self.redis_limiter.check_rate_limit(
                    key=limiter_key,
                    max_requests=max_requests,
                    window_seconds=window_seconds,
                )
                allowed = res.allowed
                remaining = res.remaining
                reset_at = res.reset_at
            except Exception:
                # Graceful fallback to in-memory on Redis error
                allowed, remaining, reset_at = self.in_memory_limiter.check_rate_limit(
                    key=limiter_key,
                    max_requests=max_requests,
                    window_seconds=window_seconds,
                )
        else:
            # In-memory sliding window
            allowed, remaining, reset_at = self.in_memory_limiter.check_rate_limit(
                key=limiter_key,
                max_requests=max_requests,
                window_seconds=window_seconds,
            )

        if not allowed:
            retry_after = max(1, int(reset_at - time.time()))
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too Many Requests. Rate limit exceeded.",
                    "error_type": "RateLimitExceeded",
                    "retry_after": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_at)),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_at))
        return response
