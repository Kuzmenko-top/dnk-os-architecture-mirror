# --- DNK-MRH-HEADER ---
# mrh_id: "skills/async_deadlock_redis/changelog.md"
# purpose: "Changelog for auto-distilled Redis connection pool async deadlock fix."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# Changelog

## [1.0.0] - 2026-08-28
- Added: Auto-fix for asyncio TimeoutError/Deadlock in Redis connection pool.
- Fixed: Added bounded connection timeout and auto-eviction policy.
- Tested: 345 regression tests passed.
