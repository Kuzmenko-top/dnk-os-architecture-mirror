/**
 * --- DNK-MRH-HEADER ---
 * mrh_id: "apps/web/src/canvas/history/undo-redo-stack.ts"
 * purpose: "High-performance UndoRedoStack engine with Ring Buffer (100) and CanvasStorageService sync."
 * canonical_source: true
 * alters_files: []
 * triggers_tasks: []
 * status: "Active"
 * version: "1.0.0"
 * updated_at: "2026-09-02"
 * author: "DNK-e.com Maksym"
 * --- END DNK-MRH-HEADER ---
 */

import type { ICommand, UndoRedoStackOptions, CommandExecutionContext } from './types';
import type { CanvasState } from '../storage/types/canvas';
import { CanvasStorageService } from '../storage/storage.service';

export class UndoRedoStack {
  private readonly undoStack: ICommand[] = [];
  private readonly redoStack: ICommand[] = [];
  private readonly maxSize: number;
  private readonly storageService?: CanvasStorageService;
  private readonly draftId: string;
  private state: CanvasState;
  private onStateChange?: (state: CanvasState) => void;

  constructor(options: UndoRedoStackOptions = {}) {
    this.maxSize = options.maxSize || 100;
    this.storageService = options.storageService;
    this.draftId = options.draftId || 'default-draft';

    this.state = options.initialState || {
      id: this.draftId,
      name: 'Untitled Canvas',
      version: 1,
      createdAt: Date.now(),
      updatedAt: Date.now(),
      viewport: { x: 0, y: 0, zoom: 1 },
      dimensions: { width: 1920, height: 1080 },
      layers: [
        {
          id: 'default-layer',
          name: 'Main Layer',
          visible: true,
          locked: false,
          opacity: 1,
          zIndex: 0,
          nodes: [],
        },
      ],
    };
  }

  public setOnStateChange(handler: (state: CanvasState) => void): void {
    this.onStateChange = handler;
  }

  public getState(): CanvasState {
    return this.state;
  }

  public setState(newState: CanvasState): void {
    this.state = newState;
    if (this.onStateChange) {
      this.onStateChange(this.state);
    }
  }

  private getExecutionContext(): CommandExecutionContext {
    return {
      state: this.state,
      storageService: this.storageService,
      onStateChange: (updatedState) => {
        this.state = updatedState;
        if (this.onStateChange) {
          this.onStateChange(this.state);
        }
      },
    };
  }

  public async execute(command: ICommand): Promise<void> {
    const ctx = this.getExecutionContext();
    await command.execute(ctx);

    this.undoStack.push(command);
    this.redoStack.length = 0; // Clear redo history upon new command execution

    // Enforce Ring Buffer invariant (max 100 commands)
    if (this.undoStack.length > this.maxSize) {
      this.undoStack.shift();
    }

    if (this.storageService) {
      const transaction = command.toTransaction(this.draftId);
      await this.storageService.saveTransaction(this.draftId, transaction);
      this.storageService.markDirty(this.draftId);
    }
  }

  public async undo(): Promise<boolean> {
    if (!this.canUndo()) return false;

    const command = this.undoStack.pop()!;
    const ctx = this.getExecutionContext();
    await command.undo(ctx);

    this.redoStack.push(command);

    if (this.storageService) {
      this.storageService.markDirty(this.draftId);
    }
    return true;
  }

  public async redo(): Promise<boolean> {
    if (!this.canRedo()) return false;

    const command = this.redoStack.pop()!;
    const ctx = this.getExecutionContext();
    await command.redo(ctx);

    this.undoStack.push(command);

    if (this.storageService) {
      this.storageService.markDirty(this.draftId);
    }
    return true;
  }

  public canUndo(): boolean {
    return this.undoStack.length > 0;
  }

  public canRedo(): boolean {
    return this.redoStack.length > 0;
  }

  public getUndoHistory(): readonly ICommand[] {
    return [...this.undoStack];
  }

  public getRedoHistory(): readonly ICommand[] {
    return [...this.redoStack];
  }

  public getUndoCount(): number {
    return this.undoStack.length;
  }

  public getRedoCount(): number {
    return this.redoStack.length;
  }

  public clear(): void {
    this.undoStack.length = 0;
    this.redoStack.length = 0;
  }
}
