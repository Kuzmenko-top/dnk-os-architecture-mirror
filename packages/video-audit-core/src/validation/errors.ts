/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/validation/errors.ts"
# purpose: "Contract Validation Errors and Format Exceptions."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

export class ValidationError extends Error {
  public readonly errors: unknown[];

  constructor(message: string, errors: unknown[] = []) {
    super(message);
    this.name = 'ValidationError';
    this.errors = errors;
    Object.setPrototypeOf(this, ValidationError.prototype);
  }
}

export class ContractValidationError extends ValidationError {
  constructor(message: string, errors: unknown[] = []) {
    super(message, errors);
    this.name = 'ContractValidationError';
    Object.setPrototypeOf(this, ContractValidationError.prototype);
  }
}

export class SchemaVersionMismatchError extends Error {
  public readonly expected: string;
  public readonly received: string;

  constructor(expected: string, received: string) {
    super(`Schema version mismatch: expected '${expected}', received '${received}'.`);
    this.name = 'SchemaVersionMismatchError';
    this.expected = expected;
    this.received = received;
    Object.setPrototypeOf(this, SchemaVersionMismatchError.prototype);
  }
}
