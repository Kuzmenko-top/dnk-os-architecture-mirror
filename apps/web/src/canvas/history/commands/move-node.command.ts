/**
 * --- DNK-MRH-HEADER ---
 * mrh_id: "apps/web/src/canvas/history/commands/move-node.command.ts"
 * purpose: "Command for moving or transforming (x, y, width, height, rotation) a node in Canvas state."
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

export interface TransformState {
  x: number;
  y: number;
  width?: number;
  height?: number;
  rotation?: number;
}

export class MoveNodeCommand implements ICommand {
  public readonly id: string;
  public readonly type = 'MOVE_NODE';
  public readonly description: string;
  public readonly timestamp: number;
  private readonly nodeId: string;
  private readonly previousTransform: TransformState;
  private readonly newTransform: TransformState;

  constructor(
    nodeId: string,
    previousTransform: TransformState,
    newTransform: TransformState,
    description?: string
  ) {
    this.id = generateUUID();
    this.timestamp = Date.now();
    this.nodeId = nodeId;
    this.previousTransform = { ...previousTransform };
    this.newTransform = { ...newTransform };
    this.description =
      description || `Move node ${nodeId} to (${newTransform.x}, ${newTransform.y})`;
  }

  public execute(context: CommandExecutionContext): void {
    for (const layer of context.state.layers) {
      const node = layer.nodes.find((n) => n.id === this.nodeId);
      if (node) {
        Object.assign(node, this.newTransform);
        break;
      }
    }
    context.state.updatedAt = Date.now();
    if (context.onStateChange) {
      context.onStateChange(context.state);
    }
  }

  public undo(context: CommandExecutionContext): void {
    for (const layer of context.state.layers) {
      const node = layer.nodes.find((n) => n.id === this.nodeId);
      if (node) {
        Object.assign(node, this.previousTransform);
        break;
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
      { op: 'replace', path: `/layers/0/nodes/${this.nodeId}/x`, value: this.newTransform.x },
      { op: 'replace', path: `/layers/0/nodes/${this.nodeId}/y`, value: this.newTransform.y },
    ];
    const inverse: CommandOperation[] = [
      { op: 'replace', path: `/layers/0/nodes/${this.nodeId}/x`, value: this.previousTransform.x },
      { op: 'replace', path: `/layers/0/nodes/${this.nodeId}/y`, value: this.previousTransform.y },
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
        from: this.previousTransform,
        to: this.newTransform,
      },
    };
  }
}
