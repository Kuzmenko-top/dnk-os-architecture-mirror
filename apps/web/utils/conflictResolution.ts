// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/utils/conflictResolution.ts"
// purpose: "Optimistic Concurrency Control (OCC), Vector Clocks & Conflict Resolution for Canvas Collaboration"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

export type OperationType =
  | 'node_create'
  | 'node_update'
  | 'node_delete'
  | 'edge_create'
  | 'edge_delete'
  | 'cursor_update';

export interface CanvasOperation {
  id: string;
  timestamp: number;
  userId: string;
  type: OperationType;
  entityId: string;
  data: Record<string, any>;
  vectorClock?: Record<string, number>;
}

export class ConflictResolver {
  private pendingOperations: CanvasOperation[] = [];
  private vectorClock: Record<string, number> = {};

  /**
   * Apply operation with Optimistic Concurrency Control (OCC).
   */
  async applyOperation(operation: CanvasOperation): Promise<{
    applied: boolean;
    operation: CanvasOperation;
    reason?: string;
  }> {
    const conflicts = this.detectConflicts(operation);

    if (conflicts.length > 0) {
      const resolved = await this.resolveConflicts(operation, conflicts);
      if (!resolved) {
        return {
          applied: false,
          operation,
          reason: 'Operation rejected due to lower priority timestamp/vector clock in conflict',
        };
      }
    }

    this.pendingOperations.push(operation);
    this.updateVectorClock(operation.userId);

    return {
      applied: true,
      operation,
    };
  }

  /**
   * Detect conflicting operations on the same entity ID.
   */
  detectConflicts(operation: CanvasOperation): CanvasOperation[] {
    return this.pendingOperations.filter((op) => {
      if (op.entityId === operation.entityId) {
        if (op.type === 'node_update' && operation.type === 'node_update') {
          return true;
        }
        if (op.type === 'node_delete' || operation.type === 'node_delete') {
          return true;
        }
      }
      return false;
    });
  }

  /**
   * Last-Write-Wins (LWW) conflict resolution strategy.
   */
  private async resolveConflicts(
    operation: CanvasOperation,
    conflicts: CanvasOperation[]
  ): Promise<boolean> {
    const latestConflict = conflicts.reduce((latest, current) => {
      return current.timestamp > latest.timestamp ? current : latest;
    });

    if (operation.timestamp > latestConflict.timestamp) {
      return true;
    }

    if (operation.timestamp === latestConflict.timestamp) {
      // Deterministic tie-breaker by userId lexicographical order
      return operation.userId > latestConflict.userId;
    }

    return false;
  }

  private updateVectorClock(userId: string): void {
    this.vectorClock[userId] = (this.vectorClock[userId] || 0) + 1;
  }

  getVectorClock(): Record<string, number> {
    return { ...this.vectorClock };
  }

  getPendingOperations(): CanvasOperation[] {
    return [...this.pendingOperations];
  }
}
