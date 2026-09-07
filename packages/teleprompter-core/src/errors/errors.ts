/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/teleprompter-core/src/errors/errors.ts"
# purpose: "Domain Exception Classes for Teleprompter Runtime and Alignment Engine."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

export class TeleprompterError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'TeleprompterError';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class ContractVersionMismatchError extends TeleprompterError {
  constructor(
    public readonly expectedVersion: string,
    public readonly actualVersion: string,
    public readonly contractType: string
  ) {
    super(
      `Contract version mismatch for ${contractType}: expected "${expectedVersion}", received "${actualVersion}".`
    );
    this.name = 'ContractVersionMismatchError';
  }
}

export class SequenceAnomalyError extends TeleprompterError {
  constructor(
    public readonly expectedMinSequence: number,
    public readonly receivedSequence: number,
    message?: string
  ) {
    super(
      message ||
        `Out-of-order or duplicate ASR hypothesis: expected sequence >= ${expectedMinSequence}, received ${receivedSequence}.`
    );
    this.name = 'SequenceAnomalyError';
  }
}

export class InvalidStateTransitionError extends TeleprompterError {
  constructor(
    public readonly currentStatus: string,
    public readonly targetStatus: string,
    public readonly context?: string
  ) {
    super(
      `Invalid state transition from "${currentStatus}" to "${targetStatus}"${context ? ` in ${context}` : ''}.`
    );
    this.name = 'InvalidStateTransitionError';
  }
}

export class TokenIndexOutOfBoundsError extends TeleprompterError {
  constructor(
    public readonly index: number,
    public readonly totalTokens: number
  ) {
    super(
      `Token index ${index} is out of bounds (total available tokens: ${totalTokens}).`
    );
    this.name = 'TokenIndexOutOfBoundsError';
  }
}
