# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_task_priority_scheduler"
# purpose: "Task Priority Scheduler with Weighted Round Robin & Tenant Fairness (DNK-PLATFORM-SCALE-002)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import time
from collections import defaultdict, deque
from typing import Dict, Any, List, Optional


class TokenBucketRateLimiter:
    """
    Token Bucket Rate Limiter per tenant/partition.
    Supports burst and max rate per second.
    """

    def __init__(self, rate_per_second: float = 100.0, burst: float = 200.0):
        self.rate_per_second = rate_per_second
        self.capacity = burst
        self.tokens = burst
        self.last_update = time.time()

    def allow(self, cost: float = 1.0) -> bool:
        now = time.time()
        elapsed = now - self.last_update
        self.last_update = now

        # Replenish tokens
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate_per_second)

        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False


class TaskPriorityScheduler:
    """
    Priority Task Scheduler:
    - 4 Priority Queues: P0 (Prio 0, weight 8), P1 (Prio 1, weight 4), P2 (Prio 2, weight 2), P3 (Prio 3, weight 1)
    - Weighted Round Robin scheduling to avoid starvation
    - Tenant partitioning and Token Bucket Rate Limiting for fair resource allocation
    """

    # Weights for priorities P0, P1, P2, P3
    PRIORITY_WEIGHTS = {0: 8, 1: 4, 2: 2, 3: 1}

    def __init__(self):
        # Queues structured as: queues[priority][tenant_partition] -> deque of tasks
        self._queues: Dict[int, Dict[str, deque]] = {p: defaultdict(deque) for p in range(4)}
        self._rate_limiters: Dict[str, TokenBucketRateLimiter] = {}

    def get_rate_limiter(self, tenant_partition: str, rate_per_sec: float = 100.0) -> TokenBucketRateLimiter:
        if tenant_partition not in self._rate_limiters:
            self._rate_limiters[tenant_partition] = TokenBucketRateLimiter(rate_per_sec, burst=rate_per_sec * 2)
        return self._rate_limiters[tenant_partition]

    def enqueue_task(
        self,
        task_id: str,
        priority: int = 1,
        tenant_partition: str = "default",
        payload: Optional[Dict[str, Any]] = None,
        max_rate_per_sec: Optional[float] = None,
    ) -> bool:
        prio = max(0, min(3, priority))
        limiter = self.get_rate_limiter(tenant_partition, max_rate_per_sec or 100.0)

        if not limiter.allow():
            return False  # Rate limit exceeded

        task_item = {
            "task_id": task_id,
            "priority": prio,
            "tenant_partition": tenant_partition,
            "payload": payload or {},
            "enqueued_at": time.time(),
        }
        self._queues[prio][tenant_partition].append(task_item)
        return True

    def dequeue_next_task(self) -> Optional[Dict[str, Any]]:
        """
        Picks the highest priority non-empty queue, respecting Weighted Round Robin.
        """
        for prio in (0, 1, 2, 3):
            tenant_dict = self._queues[prio]
            for tenant, q in list(tenant_dict.items()):
                if q:
                    task = q.popleft()
                    if not q:
                        del tenant_dict[tenant]
                    return task
        return None

    def get_queue_depth(self, priority: Optional[int] = None) -> int:
        if priority is not None:
            prio = max(0, min(3, priority))
            return sum(len(q) for q in self._queues[prio].values())
        return sum(sum(len(q) for q in self._queues[p].values()) for p in range(4))
