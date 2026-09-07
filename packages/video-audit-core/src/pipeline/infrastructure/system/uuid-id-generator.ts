/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/infrastructure/system/uuid-id-generator.ts"
# purpose: "UUID and Deterministic ID Generators."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { IdGenerator } from '../../ports/id-generator.js';
import { randomUUID } from 'node:crypto';

export class UuidIdGenerator implements IdGenerator {
  generate(prefix?: string): string {
    const id = randomUUID();
    return prefix ? `${prefix}_${id}` : id;
  }
}

export class DeterministicIdGenerator implements IdGenerator {
  private counter: number = 0;

  constructor(private readonly basePrefix: string = 'test') {}

  generate(prefix?: string): string {
    this.counter += 1;
    const p = prefix || this.basePrefix;
    return `${p}_${this.counter.toString().padStart(4, '0')}`;
  }

  reset(): void {
    this.counter = 0;
  }
}
