# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/security/rate_limiter.py"
# purpose: "Redis-based sliding window rate limiter middleware for DDOS and brute-force protection."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import time
from dataclasses import dataclass
from typing import Tuple
import redis


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    reset_at: float


class RateLimiter:
    """
    Redis-based rate limiting middleware.

    Features:
    - Sliding window algorithm
    - Per-user or per-IP limits
    - Configurable limits (requests/minute, requests/hour)
    - Automatic cleanup of expired keys
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)

    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> RateLimitResult:
        """
        Check if request is within rate limit.

        Args:
            key: User ID or IP address
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds

        Returns:
            RateLimitResult(allowed, remaining, reset_at)
        """
        now = time.time()
        window_start = now - window_seconds

        # Sliding window: remove old entries
        self.redis.zremrangebyscore(key, 0, window_start)

        # Count current requests
        current_count = self.redis.zcard(key)

        if current_count >= max_requests:
            # Rate limit exceeded
            oldest = self.redis.zrange(key, 0, 0, withscores=True)
            reset_at = oldest[0][1] + window_seconds if oldest else now + window_seconds

            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=reset_at,
            )

        # Add current request with unique member
        member = f"{now}:{time.time_ns()}"
        self.redis.zadd(key, {member: now})
        self.redis.expire(key, window_seconds * 2)  # TTL

        remaining = max_requests - current_count - 1
        reset_at = now + window_seconds

        return RateLimitResult(
            allowed=True,
            remaining=remaining,
            reset_at=reset_at,
        )

    def get_usage(self, key: str, window_seconds: int) -> Tuple[int, int]:
        """
        Get current usage stats.

        Returns:
            (current_count, max_requests)
        """
        now = time.time()
        window_start = now - window_seconds

        self.redis.zremrangebyscore(key, 0, window_start)
        current_count = self.redis.zcard(key)

        return current_count, 0  # Max unknown without config
