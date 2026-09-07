/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/infrastructure/contracts/redis-contract.ts"
# purpose: "Redis Queue & PubSub Keys and Lua Script Contract for High-Throughput Leases."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

export const REDIS_KEYS = {
  jobQueue: (type: string) => `video_audit:queue:${type}`,
  jobData: (jobId: string) => `video_audit:job:${jobId}`,
  idempotencyIndex: (key: string) => `video_audit:idemp:${key}`,
  workerHeartbeat: (workerId: string) => `video_audit:worker:${workerId}`,
  eventsStream: 'video_audit:events:stream'
};

export const REDIS_ATOMIC_LEASE_LUA = `
-- KEYS[1]: ZSET queue key (sorted by available_at)
-- KEYS[2]: HASH prefix for job data
-- ARGV[1]: workerId
-- ARGV[2]: nowTimestampMs
-- ARGV[3]: leaseDurationMs

local candidate = redis.call('ZRANGEBYSCORE', KEYS[1], '-inf', ARGV[2], 'LIMIT', 0, 1)
if #candidate == 0 then
    return nil
end

local jobId = candidate[1]
local jobKey = KEYS[2] .. ':' .. jobId

local currentStatus = redis.call('HGET', jobKey, 'status')
if currentStatus == 'queued' then
    local leasedUntilMs = tonumber(ARGV[2]) + tonumber(ARGV[3])
    redis.call('HSET', jobKey, 'status', 'leased', 'leasedBy', ARGV[1], 'leasedUntil', leasedUntilMs)
    redis.call('ZREM', KEYS[1], jobId)
    return jobId
else
    -- Out of sync, remove stale entry from queue
    redis.call('ZREM', KEYS[1], jobId)
    return nil
end
`;
