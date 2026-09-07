/*
# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/infrastructure/llm/shared/provider-errors.ts"
# purpose: "Provider-Neutral Error Classification and Mapping Hierarchy."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

export class ProviderError extends Error {
  constructor(
    message: string,
    public readonly providerId: string,
    public readonly originalError?: unknown
  ) {
    super(message);
    this.name = this.constructor.name;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export abstract class RetryableProviderError extends ProviderError {
  public abstract readonly backoffSuggestMs?: number;
}

export abstract class PermanentProviderError extends ProviderError {}

export class RateLimitError extends RetryableProviderError {
  constructor(
    message: string,
    providerId: string,
    public readonly backoffSuggestMs?: number,
    originalError?: unknown
  ) {
    super(message, providerId, originalError);
  }
}

export class TimeoutError extends RetryableProviderError {
  public readonly backoffSuggestMs = 1000;
  constructor(message: string, providerId: string, originalError?: unknown) {
    super(message, providerId, originalError);
  }
}

export class TemporaryServerError extends RetryableProviderError {
  public readonly backoffSuggestMs = 2000;
  constructor(message: string, providerId: string, originalError?: unknown) {
    super(message, providerId, originalError);
  }
}

export class InvalidCredentialsError extends PermanentProviderError {
  constructor(message: string, providerId: string, originalError?: unknown) {
    super(message, providerId, originalError);
  }
}

export class InvalidModelError extends PermanentProviderError {
  constructor(message: string, providerId: string, originalError?: unknown) {
    super(message, providerId, originalError);
  }
}

export class ContextOverflowError extends PermanentProviderError {
  constructor(message: string, providerId: string, originalError?: unknown) {
    super(message, providerId, originalError);
  }
}

export class ContentPolicyError extends PermanentProviderError {
  constructor(message: string, providerId: string, originalError?: unknown) {
    super(message, providerId, originalError);
  }
}

export class SchemaViolationError extends RetryableProviderError {
  public readonly backoffSuggestMs = 0; // immediate feedback retry
  constructor(
    message: string,
    providerId: string,
    public readonly validationFeedback?: string[],
    originalError?: unknown
  ) {
    super(message, providerId, originalError);
  }
}

export class HallucinationError extends PermanentProviderError {
  constructor(message: string, providerId: string, originalError?: unknown) {
    super(message, providerId, originalError);
  }
}

export class OversizedOutputError extends PermanentProviderError {
  constructor(message: string, providerId: string, originalError?: unknown) {
    super(message, providerId, originalError);
  }
}

export class NetworkFailureError extends RetryableProviderError {
  public readonly backoffSuggestMs = 1500;
  constructor(message: string, providerId: string, originalError?: unknown) {
    super(message, providerId, originalError);
  }
}
