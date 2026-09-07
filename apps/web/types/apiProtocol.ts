// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_types_api_protocol"
// purpose: "Canonical API Result, Error Envelope, and Transport Protocol for apps/web Tier-1 & Tier-2"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-06"
// author: "DNK-e.com Maksym & Gerych Prime"
// --- END DNK-MRH-HEADER ---

export interface ApiError {
  code: string;
  message: string;
  status?: number;
  details?: Record<string, unknown> | null;
  timestamp?: string;
}

export type Result<T, E = ApiError> =
  | { ok: true; data: T; error?: never }
  | { ok: false; error: E; data?: never };

export const ok = <T, E = ApiError>(data: T): Result<T, E> => ({
  ok: true,
  data,
});

export const err = <T = never, E = ApiError>(error: E): Result<T, E> => ({
  ok: false,
  error,
});

export function normalizeError(error: unknown, fallbackMessage = 'An unexpected error occurred'): ApiError {
  if (typeof error === 'object' && error !== null && 'message' in error && typeof (error as any).message === 'string') {
    const errObj = error as Record<string, unknown>;
    return {
      code: typeof errObj.code === 'string' ? errObj.code : 'CLIENT_ERROR',
      message: errObj.message as string,
      status: typeof errObj.status === 'number' ? errObj.status : undefined,
      details: (errObj.details as Record<string, unknown>) || null,
      timestamp: new Date().toISOString(),
    };
  }

  if (typeof error === 'string') {
    return {
      code: 'GENERIC_STRING_ERROR',
      message: error,
      timestamp: new Date().toISOString(),
    };
  }

  return {
    code: 'UNKNOWN_ERROR',
    message: fallbackMessage,
    timestamp: new Date().toISOString(),
  };
}

export async function safeAsync<T>(
  promise: Promise<T>,
  fallbackMessage?: string
): Promise<Result<T, ApiError>> {
  try {
    const data = await promise;
    return ok(data);
  } catch (error: unknown) {
    return err(normalizeError(error, fallbackMessage));
  }
}

// Re-export generated OpenAPI contracts & schema dictionary
export type { paths as ApiPaths, components as ApiComponents, operations as ApiOperations } from './apiGenerated';
export type ApiSchemas = import('./apiGenerated').components['schemas'];

