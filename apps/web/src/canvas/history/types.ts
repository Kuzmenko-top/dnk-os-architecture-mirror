/**
 * --- DNK-MRH-HEADER ---
 * mrh_id: "apps/web/src/canvas/history/types.ts"
 * purpose: "History and Command Execution context types, command interfaces, and undo/redo metadata."
 * canonical_source: true
 * alters_files: []
 * triggers_tasks: []
 * status: "Active"
 * version: "1.0.0"
 * updated_at: "2026-09-02"
 * author: "DNK-e.com Maksym"
 * --- END DNK-MRH-HEADER ---
 */

import type { CanvasState } from '../storage/types/canvas';
import type { CommandOperation, Transaction } from '../storage/types/history';
import type { CanvasStorageService } from '../storage/storage.service';

export interface CommandExecutionContext {
  state: CanvasState;
  storageService?: CanvasStorageService;
  onStateChange?: (state: CanvasState) => void;
}

export interface ICommand {
  readonly id: string;
  readonly type: string;
  readonly description: string;
  readonly timestamp: number;

  execute(context: CommandExecutionContext): Promise<void> | void;
  undo(context: CommandExecutionContext): Promise<void> | void;
  redo(context: CommandExecutionContext): Promise<void> | void;

  getPatches?(): { forward: CommandOperation[]; inverse: CommandOperation[] };
  toTransaction(draftId?: string): Transaction;
}

export interface UndoRedoStackOptions {
  maxSize?: number; // Ring buffer max size (default 100)
  storageService?: CanvasStorageService;
  draftId?: string;
  initialState?: CanvasState;
}
