/**
 * --- DNK-MRH-HEADER ---
 * mrh_id: "apps/web/src/canvas/history/commands/delete-node.command.ts"
 * purpose: "Command for deleting a node from Canvas state with full undo restoration."
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
import type { NodeProperties } from '../../storage/types/canvas';
import type { Transaction, CommandOperation } from '../../storage/types/history';

export class DeleteNodeCommand implements ICommand {
  public readonly id: string;
  public readonly type = 'DELETE_NODE';
  public readonly description: string;
  public readonly timestamp: number;
  private readonly nodeId: string;
  private deletedNode: NodeProperties | null = null;
  private targetLayerId: string | null = null;
  private originalIndex = -1;

  constructor(nodeId: string, description?: string) {
    this.id = generateUUID();
    this.timestamp = Date.now();
    this.nodeId = nodeId;
    this.description = description || `Delete node ${nodeId}`;
  }

  public execute(context: CommandExecutionContext): void {
    for (const layer of context.state.layers) {
      const idx = layer.nodes.findIndex((n) => n.id === this.nodeId);
      if (idx >= 0) {
        this.deletedNode = { ...layer.nodes[idx] };
        this.targetLayerId = layer.id;
        this.originalIndex = idx;
        layer.nodes.splice(idx, 1);
        break;
      }
    }
    context.state.updatedAt = Date.now();
    if (context.onStateChange) {
      context.onStateChange(context.state);
    }
  }

  public undo(context: CommandExecutionContext): void {
    if (!this.deletedNode || !this.targetLayerId) return;

    let layer = context.state.layers.find((l) => l.id === this.targetLayerId);
    if (!layer && context.state.layers.length > 0) {
      layer = context.state.layers[0];
    }

    if (layer) {
      if (this.originalIndex >= 0 && this.originalIndex <= layer.nodes.length) {
        layer.nodes.splice(this.originalIndex, 0, { ...this.deletedNode });
      } else {
        layer.nodes.push({ ...this.deletedNode });
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
    const forward: CommandOperation[] = [{ op: 'remove', path: `/layers/0/nodes/${this.nodeId}` }];
    const inverse: CommandOperation[] = [
      { op: 'add', path: `/layers/0/nodes/${this.originalIndex}`, value: this.deletedNode },
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
        nodeId: this.nodeId,
        layerId: this.targetLayerId,
      },
    };
  }
}
