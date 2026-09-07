/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/ports/telegram-update-tracker.ts"
# purpose: "Port Interface for Telegram Event Update Idempotency Tracking."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

export interface TelegramUpdateTrackerPort {
  isUpdateProcessed(updateId: number): Promise<{ processed: boolean; referenceAssetId?: string }>;
  recordUpdate(updateId: number, referenceAssetId: string): Promise<void>;
}
