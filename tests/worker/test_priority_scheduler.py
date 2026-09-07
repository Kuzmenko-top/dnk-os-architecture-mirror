# --- DNK-MRH-HEADER ---
# mrh_id: "tests_worker_test_priority_scheduler"
# purpose: "Unit Tests for Task Priority Scheduler & Rate Limiter (DNK-PLATFORM-SCALE-002)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.task_priority_scheduler import TaskPriorityScheduler, TokenBucketRateLimiter


def test_enqueue_and_dequeue_by_priority():
    scheduler = TaskPriorityScheduler()

    # Enqueue low priority task (P3) first, then high priority (P0)
    scheduler.enqueue_task("task-low", priority=3, tenant_partition="tenant-a")
    scheduler.enqueue_task("task-high", priority=0, tenant_partition="tenant-a")

    # Dequeue should yield task-high (P0) first!
    t1 = scheduler.dequeue_next_task()
    t2 = scheduler.dequeue_next_task()

    assert t1 is not None and t1["task_id"] == "task-high"
    assert t2 is not None and t2["task_id"] == "task-low"


def test_token_bucket_rate_limiter():
    limiter = TokenBucketRateLimiter(rate_per_second=2.0, burst=2.0)

    assert limiter.allow() is True
    assert limiter.allow() is True
    assert limiter.allow() is False  # rate limited!


def test_queue_depth_by_priority():
    scheduler = TaskPriorityScheduler()

    scheduler.enqueue_task("t1", priority=1, tenant_partition="tenant-1")
    scheduler.enqueue_task("t2", priority=1, tenant_partition="tenant-1")
    scheduler.enqueue_task("t3", priority=2, tenant_partition="tenant-2")

    assert scheduler.get_queue_depth(priority=1) == 2
    assert scheduler.get_queue_depth(priority=2) == 1
    assert scheduler.get_queue_depth(priority=0) == 0
    assert scheduler.get_queue_depth() == 3
