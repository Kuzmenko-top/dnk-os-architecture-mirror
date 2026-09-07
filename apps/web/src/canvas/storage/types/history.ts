/**
 * --- DNK-MRH-HEADER ---
 * mrh_id: "apps/web/src/canvas/storage/types/history.ts"
 * purpose: "Transaction, JSON patch operations, ring buffer and differential snapshot types for DNK OS Canvas Engine."
 * canonical_source: true
 * alters_files: []
 * triggers_tasks: []
 * status: "Active"
 * version: "1.0.0"
 * updated_at: "2026-09-02"
 * author: "DNK-e.com Maksym & Gerych"
 * --- END DNK-MRH-HEADER ---
 */

import { CanvasState } from './canvas';

export type PatchOp = 'add' | 'remove' | 'replace' | 'move' | 'copy' | 'test';

export interface CommandOperation {
  op: PatchOp;
  path: string;
  value?: unknown;
  from?: string;
}

export interface DifferentialSnapshot {
  baseSnapshotId: string;
  targetSnapshotId: string;
  forwardPatches: CommandOperation[];
  inversePatches: CommandOperation[];
  timestamp: number;
  version: number;
  checksum?: string;
}

export interface Transaction {
  id: string;
  draftId: string;
  sequenceNumber: number;
  timestamp: number;
  description: string;
  forwardPatches: CommandOperation[];
  inversePatches: CommandOperation[];
  metadata?: Record<string, unknown>;
}

export interface DraftRecord {
  id: string;
  name: string;
  state: CanvasState;
  isDifferential?: boolean;
  baseDraftId?: string | null;
  differentialSnapshot?: DifferentialSnapshot;
  checksum: string;
  createdAt: number;
  updatedAt: number;
}

export interface RingBufferStats {
  draftId: string;
  totalRecorded: number;
  currentCount: number;
  oldestSequenceNumber: number;
  newestSequenceNumber: number;
  capacity: number;
}

export interface CrashRecoveryResult {
  recovered: boolean;
  draftId: string | null;
  state: CanvasState | null;
  replayedTransactionsCount: number;
  lastSequenceNumber: number;
  reason?: string;
}
