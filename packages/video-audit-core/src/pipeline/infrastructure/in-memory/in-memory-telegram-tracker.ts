/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/infrastructure/in-memory/in-memory-telegram-tracker.ts"
# purpose: "In-Memory Implementation of Telegram Event Update Idempotency Tracker."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { TelegramUpdateTrackerPort } from '../../ports/telegram-update-tracker.js';

export class InMemoryTelegramUpdateTracker implements TelegramUpdateTrackerPort {
  private readonly processedUpdates = new Map<number, string>();

  async isUpdateProcessed(
    updateId: number
  ): Promise<{ processed: boolean; referenceAssetId?: string }> {
    const referenceAssetId = this.processedUpdates.get(updateId);
    if (referenceAssetId) {
      return { processed: true, referenceAssetId };
    }
    return { processed: false };
  }

  async recordUpdate(updateId: number, referenceAssetId: string): Promise<void> {
    this.processedUpdates.set(updateId, referenceAssetId);
  }

  async clear(): Promise<void> {
    this.processedUpdates.clear();
  }
}

export { InMemoryTelegramUpdateTracker as InMemoryTelegramTracker };
