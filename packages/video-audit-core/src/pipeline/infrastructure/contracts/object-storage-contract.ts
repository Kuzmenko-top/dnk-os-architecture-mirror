/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/infrastructure/contracts/object-storage-contract.ts"
# purpose: "S3 / GCS / MinIO S3-Compatible Object Storage Topology Specification."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

export const S3_STORAGE_TOPOLOGY = {
  bucketPrefix: 'dnk-video-audit',
  buckets: {
    sources: 'dnk-video-audit-sources',
    transcripts: 'dnk-video-audit-transcripts',
    scenes: 'dnk-video-audit-scenes',
    ocr: 'dnk-video-audit-ocr',
    audio: 'dnk-video-audit-audio',
    evaluations: 'dnk-video-audit-evaluations',
    reports: 'dnk-video-audit-reports',
    adaptations: 'dnk-video-audit-adaptations'
  },
  headers: {
    sha256ChecksumHeader: 'x-amz-meta-sha256',
    schemaVersionHeader: 'x-amz-meta-schema-version',
    jobIdHeader: 'x-amz-meta-job-id'
  }
};
