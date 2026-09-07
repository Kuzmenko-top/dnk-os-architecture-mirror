/**
 * --- DNK-MRH-HEADER ---
 * mrh_id: "apps/web/src/canvas/history/commands/reorder-layer.command.ts"
 * purpose: "Command for reordering layer zIndex or node zIndex within a layer."
 * canonical_source: true
 * alters_files: []
 * triggers_tasks: []
 * status: "Active"
 * version: "1.0.0"
 * updated_at: "2026-09-02"
 * author: "DNK-e.com Maksym"
 * --- END DNK-MRH-HEADER ---
 */

import { generateUUID } from '../../storage/storage.service';
import type { ICommand, CommandExecutionContext } from '../types';
import type { Transaction, CommandOperation } from '../../storage/types/history';

export class ReorderLayerCommand implements ICommand {
  public readonly id: string;
  public readonly type = 'REORDER_LAYER';
  public readonly description: string;
  public readonly timestamp: number;
  private readonly targetId: string;
  private readonly isLayer: boolean;
  private readonly oldIndex: number;
  private readonly newIndex: number;

  constructor(targetId: string, oldIndex: number, newIndex: number, isLayer = false, description?: string) {
    this.id = generateUUID();
    this.timestamp = Date.now();
    this.targetId = targetId;
    this.oldIndex = oldIndex;
    this.newIndex = newIndex;
    this.isLayer = isLayer;
    this.description = description || `Reorder ${isLayer ? 'layer' : 'node'} ${targetId} from index ${oldIndex} to ${newIndex}`;
  }

  public execute(context: CommandExecutionContext): void {
    if (this.isLayer) {
      const layers = context.state.layers;
      const idx = layers.findIndex((l) => l.id === this.targetId);
      if (idx >= 0 && this.newIndex >= 0 && this.newIndex < layers.length) {
        const [removed] = layers.splice(idx, 1);
        layers.splice(this.newIndex, 0, removed);
        layers.forEach((l, i) => (l.zIndex = i));
      }
    } else {
      for (const layer of context.state.layers) {
        const idx = layer.nodes.findIndex((n) => n.id === this.targetId);
        if (idx >= 0 && this.newIndex >= 0 && this.newIndex < layer.nodes.length) {
          const [removed] = layer.nodes.splice(idx, 1);
          layer.nodes.splice(this.newIndex, 0, removed);
          layer.nodes.forEach((n, i) => (n.zIndex = i));
          break;
        }
      }
    }
    context.state.updatedAt = Date.now();
    if (context.onStateChange) {
      context.onStateChange(context.state);
    }
  }

  public undo(context: CommandExecutionContext): void {
    if (this.isLayer) {
      const layers = context.state.layers;
      const idx = layers.findIndex((l) => l.id === this.targetId);
      if (idx >= 0 && this.oldIndex >= 0 && this.oldIndex < layers.length) {
        const [removed] = layers.splice(idx, 1);
        layers.splice(this.oldIndex, 0, removed);
        layers.forEach((l, i) => (l.zIndex = i));
      }
    } else {
      for (const layer of context.state.layers) {
        const idx = layer.nodes.findIndex((n) => n.id === this.targetId);
        if (idx >= 0 && this.oldIndex >= 0 && this.oldIndex < layer.nodes.length) {
          const [removed] = layer.nodes.splice(idx, 1);
          layer.nodes.splice(this.oldIndex, 0, removed);
          layer.nodes.forEach((n, i) => (n.zIndex = i));
          break;
        }
      }
    }
    context.state.updatedAt = Date.now();
    if (context.onStateChange) {
      context.onStateChange(context.state);
    }
  }

  public redo(context: CommandExecutionContext): void {
    this.execute(context);
  }

  public getPatches(): { forward: CommandOperation[]; inverse: CommandOperation[] } {
    const forward: CommandOperation[] = [
      { op: 'move', path: `/layers/0/nodes/${this.newIndex}`, from: `/layers/0/nodes/${this.oldIndex}` },
    ];
    const inverse: CommandOperation[] = [
      { op: 'move', path: `/layers/0/nodes/${this.oldIndex}`, from: `/layers/0/nodes/${this.newIndex}` },
    ];
    return { forward, inverse };
  }

  public toTransaction(draftId = 'default-draft'): Transaction {
    const patches = this.getPatches();
    return {
      id: this.id,
      draftId,
      sequenceNumber: 0,
      timestamp: this.timestamp,
      description: this.description,
      forwardPatches: patches.forward,
      inversePatches: patches.inverse,
      metadata: {
        commandType: this.type,
        targetId: this.targetId,
        isLayer: this.isLayer,
        fromIndex: this.oldIndex,
        toIndex: this.newIndex,
      },
    };
  }
}
