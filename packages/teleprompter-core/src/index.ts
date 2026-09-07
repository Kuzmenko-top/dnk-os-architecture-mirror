/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/teleprompter-core/src/index.ts"
# purpose: "Main Entrypoint and Public API Exports for Teleprompter Core."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

// Domain
export * from './domain/tokens.js';
export * from './domain/session.js';
export * from './domain/events.js';

// Ports
export * from './ports/asr.js';
export * from './ports/normalizer.js';

// State
export * from './state/token-state.js';
export * from './state/session-machine.js';

// Alignment
export * from './alignment/matcher.js';
export * from './alignment/engine.js';

// Pacing
export * from './pacing/wpm.js';

// Analytics
export * from './analytics/collector.js';

// Errors
export * from './errors/errors.js';
