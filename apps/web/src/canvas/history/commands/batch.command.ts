/**
 * --- DNK-MRH-HEADER ---
 * mrh_id: "apps/web/src/canvas/history/commands/batch.command.ts"
 * purpose: "BatchCommand for aggregating multiple atomic sub-commands into a single macro transaction."
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

export class BatchCommand implements ICommand {
  public readonly id: string;
  public readonly type = 'BATCH_COMMAND';
  public readonly description: string;
  public readonly timestamp: number;
  private readonly commands: ICommand[];

  constructor(commands: ICommand[], description?: string) {
    this.id = generateUUID();
    this.timestamp = Date.now();
    this.commands = [...commands];
    this.description = description || `Batch operation (${commands.length} actions)`;
  }

  public execute(context: CommandExecutionContext): void {
    for (const cmd of this.commands) {
      cmd.execute(context);
    }
  }

  public undo(context: CommandExecutionContext): void {
    // Reverse order undo for sub-commands
    for (let i = this.commands.length - 1; i >= 0; i--) {
      this.commands[i].undo(context);
    }
  }

  public redo(context: CommandExecutionContext): void {
    for (const cmd of this.commands) {
      cmd.redo(context);
    }
  }

  public getPatches(): { forward: CommandOperation[]; inverse: CommandOperation[] } {
    const forward: CommandOperation[] = [];
    const inverse: CommandOperation[] = [];

    for (const cmd of this.commands) {
      if (cmd.getPatches) {
        const { forward: f, inverse: inv } = cmd.getPatches();
        forward.push(...f);
        inverse.unshift(...inv);
      }
    }
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
        subCommandsCount: this.commands.length,
        subCommandsTypes: this.commands.map((c) => c.type),
      },
    };
  }
}
