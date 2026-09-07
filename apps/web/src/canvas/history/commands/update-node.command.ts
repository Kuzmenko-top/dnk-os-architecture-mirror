/**
 * --- DNK-MRH-HEADER ---
 * mrh_id: "apps/web/src/canvas/history/commands/update-node.command.ts"
 * purpose: "Command for updating properties of an existing node in Canvas state."
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

export class UpdateNodeCommand implements ICommand {
  public readonly id: string;
  public readonly type = 'UPDATE_NODE';
  public readonly description: string;
  public readonly timestamp: number;
  private readonly nodeId: string;
  private readonly newProps: Partial<NodeProperties>;
  private previousProps: NodeProperties | null = null;

  constructor(nodeId: string, newProps: Partial<NodeProperties>, description?: string) {
    this.id = generateUUID();
    this.timestamp = Date.now();
    this.nodeId = nodeId;
    this.newProps = { ...newProps };
    this.description = description || `Update node ${nodeId}`;
  }

  public execute(context: CommandExecutionContext): void {
    for (const layer of context.state.layers) {
      const node = layer.nodes.find((n) => n.id === this.nodeId);
      if (node) {
        if (!this.previousProps) {
          this.previousProps = { ...node };
        }
        Object.assign(node, this.newProps);
        break;
      }
    }
    context.state.updatedAt = Date.now();
    if (context.onStateChange) {
      context.onStateChange(context.state);
    }
  }

  public undo(context: CommandExecutionContext): void {
    if (!this.previousProps) return;
    for (const layer of context.state.layers) {
      const nodeIndex = layer.nodes.findIndex((n) => n.id === this.nodeId);
      if (nodeIndex >= 0) {
        layer.nodes[nodeIndex] = { ...this.previousProps };
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
      { op: 'replace', path: `/layers/0/nodes/${this.nodeId}`, value: this.newProps },
    ];
    const inverse: CommandOperation[] = [
      { op: 'replace', path: `/layers/0/nodes/${this.nodeId}`, value: this.previousProps || {} },
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
        changes: this.newProps,
      },
    };
  }
}
