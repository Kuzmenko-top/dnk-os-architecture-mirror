/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/infrastructure/contracts/postgres-contract.ts"
# purpose: "PostgreSQL Production Schema & Migration Contract Specification for Audit Jobs."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

export const POSTGRES_AUDIT_JOBS_DDL = `
-- Video Audit Jobs Table
CREATE TABLE IF NOT EXISTS video_audit_jobs (
    id VARCHAR(64) PRIMARY KEY,
    reference_asset_id VARCHAR(64) NOT NULL,
    job_type VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    attempt INT NOT NULL DEFAULT 1,
    max_attempts INT NOT NULL DEFAULT 5,
    idempotency_key VARCHAR(256) NOT NULL UNIQUE,
    input_artifact_keys JSONB NOT NULL DEFAULT '[]'::jsonb,
    output_artifact_keys JSONB NOT NULL DEFAULT '[]'::jsonb,
    schema_version VARCHAR(32) NOT NULL DEFAULT 'audit-job.v1',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    available_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    leased_until TIMESTAMPTZ,
    leased_by VARCHAR(64),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    last_error JSONB
);

CREATE INDEX IF NOT EXISTS idx_audit_jobs_poll ON video_audit_jobs (status, available_at)
WHERE status = 'queued';

CREATE INDEX IF NOT EXISTS idx_audit_jobs_leases ON video_audit_jobs (status, leased_until)
WHERE status = 'leased';

CREATE INDEX IF NOT EXISTS idx_audit_jobs_ref_id ON video_audit_jobs (reference_asset_id);

-- Job Transitions Audit Log Table
CREATE TABLE IF NOT EXISTS video_audit_job_transitions (
    id BIGSERIAL PRIMARY KEY,
    job_id VARCHAR(64) NOT NULL REFERENCES video_audit_jobs(id) ON DELETE CASCADE,
    from_status VARCHAR(32) NOT NULL,
    to_status VARCHAR(32) NOT NULL,
    actor_id VARCHAR(64) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reason TEXT,
    attempt INT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_job_transitions_job ON video_audit_job_transitions (job_id, timestamp);
`;
