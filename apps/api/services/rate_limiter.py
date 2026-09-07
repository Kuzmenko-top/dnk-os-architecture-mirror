# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/rate_limiter.py"
# purpose: "Token-Bucket Rate Limiter with burst capacity and async context manager support"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import asyncio
import time
from typing import Optional


class TokenBucketRateLimiter:
    """
    Token-Bucket Rate Limiter for API clients (e.g. Shopify Admin API: 1000 req/min, burst 50).
    """

    def __init__(self, rate: float = 1000.0, burst: float = 50.0):
        self.rate = float(rate)  # tokens per minute
        self.burst = float(burst)  # maximum bucket size
        self.tokens = float(burst)
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, cost: float = 1.0) -> None:
        """Acquires `cost` tokens, waiting asynchronously if necessary."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            fill_rate_per_sec = self.rate / 60.0
            self.tokens = min(self.burst, self.tokens + elapsed * fill_rate_per_sec)
            self.last_update = now

            if self.tokens < cost:
                needed = cost - self.tokens
                wait_time = needed / fill_rate_per_sec
                await asyncio.sleep(wait_time)
                # After sleeping, replenish tokens and deduct cost
                now_after = time.monotonic()
                elapsed_after = now_after - self.last_update
                self.tokens = min(self.burst, self.tokens + elapsed_after * fill_rate_per_sec)
                self.last_update = now_after
                self.tokens -= cost
            else:
                self.tokens -= cost

    async def __aenter__(self):
        await self.acquire(cost=1.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
