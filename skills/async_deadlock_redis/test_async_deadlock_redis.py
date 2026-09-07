# --- DNK-MRH-HEADER ---
# mrh_id: "skills/async_deadlock_redis/test_async_deadlock_redis.py"
# purpose: "Unit tests for Redis connection pool anti-deadlock wrapper."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import asyncio
import pytest
from skills.async_deadlock_redis.solution import execute_with_anti_deadlock


@pytest.mark.asyncio
async def test_anti_deadlock_success():
    async def quick_coro():
        return "success"
    result = await execute_with_anti_deadlock(quick_coro, timeout_seconds=1.0)
    assert result == "success"


@pytest.mark.asyncio
async def test_anti_deadlock_timeout_fallback():
    async def hanging_coro():
        await asyncio.sleep(2.0)
        return "late"
    result = await execute_with_anti_deadlock(hanging_coro, timeout_seconds=0.1)
    assert result.get("status") == "error"
    assert "Anti-Deadlock" in result.get("error", "")
