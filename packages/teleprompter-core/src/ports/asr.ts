/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/teleprompter-core/src/ports/asr.ts"
# purpose: "ASR Provider Port and Hypothesis Contracts."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

export interface ASRWord {
  word: string;
  startMs: number;
  endMs: number;
  confidence?: number;
}

export interface ASRHypothesis {
  /**
   * Monotonically increasing sequence number.
   * Protects the runtime from processing out-of-order or duplicate worker events.
   */
  sequence: number;
  text: string;
  words?: ASRWord[];
  isFinal: boolean;
  confidence?: number;
  startedAtMs: number;
  endedAtMs: number;
}

export interface ASRCapabilities {
  supportsWordTimestamps: boolean;
  supportsInterimResults: boolean;
  supportsConfidence: boolean;
  sampleRates: number[];
  language: string;
}

export interface ASRStartOptions {
  language?: string;
  sampleRate?: number;
  interimResults?: boolean;
}

export interface ASRProviderPort {
  readonly id: string;
  readonly capabilities: ASRCapabilities;

  start(options?: ASRStartOptions): Promise<void>;
  stop(): Promise<void>;
  subscribe(listener: (hypothesis: ASRHypothesis) => void): () => void;
}
