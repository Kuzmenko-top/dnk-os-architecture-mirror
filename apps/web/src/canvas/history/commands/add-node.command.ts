/**
 * --- DNK-MRH-HEADER ---
 * mrh_id: "apps/web/src/canvas/history/commands/add-node.command.ts"
 * purpose: "Command implementation for adding a new node to Canvas state."
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

export class AddNodeCommand implements ICommand {
  public readonly id: string;
  public readonly type = 'ADD_NODE';
  public readonly description: string;
  public readonly timestamp: number;
  private readonly targetLayerId: string;
  private readonly nodeProps: NodeProperties;

  constructor(nodeProps: NodeProperties, targetLayerId = 'default-layer', description?: string) {
    this.id = generateUUID();
    this.timestamp = Date.now();
    this.nodeProps = { ...nodeProps };
    this.targetLayerId = targetLayerId;
    this.description = description || `Add node ${nodeProps.name || nodeProps.id} (${nodeProps.type})`;
  }

  public execute(context: CommandExecutionContext): void {
    let layer = context.state.layers.find((l) => l.id === this.targetLayerId);
    if (!layer) {
      if (context.state.layers.length > 0) {
        layer = context.state.layers[0];
      } else {
        layer = {
          id: 'default-layer',
          name: 'Main Layer',
          visible: true,
          locked: false,
          opacity: 1,
          zIndex: 0,
          nodes: [],
        };
        context.state.layers.push(layer);
      }
    }

    const existingIndex = layer.nodes.findIndex((n) => n.id === this.nodeProps.id);
    if (existingIndex >= 0) {
      layer.nodes[existingIndex] = { ...this.nodeProps };
    } else {
      layer.nodes.push({ ...this.nodeProps });
    }

    context.state.updatedAt = Date.now();
    if (context.onStateChange) {
      context.onStateChange(context.state);
    }
  }

  public undo(context: CommandExecutionContext): void {
    for (const layer of context.state.layers) {
      const idx = layer.nodes.findIndex((n) => n.id === this.nodeProps.id);
      if (idx >= 0) {
        layer.nodes.splice(idx, 1);
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
    const forward: CommandOperation[] = [{ op: 'add', path: `/layers/0/nodes/-`, value: this.nodeProps }];
    const inverse: CommandOperation[] = [{ op: 'remove', path: `/layers/0/nodes/${this.nodeProps.id}` }];
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
        targetId: this.nodeProps.id,
        targetLayerId: this.targetLayerId,
      },
    };
  }
}
