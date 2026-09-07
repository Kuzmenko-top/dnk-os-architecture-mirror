/*
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/adapters/teleprompter/web-speech-provider.ts"
// purpose: "Web Speech API ASR Provider & Deterministic Mock Fallback Provider implementing ASRProviderPort."
// canonical_source: true
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---
*/

import type {
  ASRProviderPort,
  ASRHypothesis,
  ASRCapabilities,
  ASRStartOptions,
  RuntimeToken,
} from '@dnk/teleprompter-core';

interface SpeechRecognitionEvent {
  resultIndex: number;
  results: {
    length: number;
    [index: number]: {
      isFinal: boolean;
      length: number;
      [index: number]: {
        transcript: string;
        confidence: number;
      };
    };
  };
}

interface SpeechRecognitionInstance {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: { error: string; message?: string }) => void) | null;
  onend: (() => void) | null;
}

export class WebSpeechProvider implements ASRProviderPort {
  readonly id = 'web-speech-api';
  private recognition: SpeechRecognitionInstance | null = null;
  private sequence = 0;
  private sessionStartTime = 0;
  private isRunning = false;
  private listeners: Set<(hypothesis: ASRHypothesis) => void> = new Set();
  private language: string;

  constructor(options?: { language?: string }) {
    this.language = options?.language ?? 'uk-UA';
  }

  get capabilities(): ASRCapabilities {
    return {
      supportsWordTimestamps: false,
      supportsConfidence: true,
      supportsInterimResults: true,
      sampleRates: [16000, 44100, 48000],
      language: this.language,
    };
  }

  subscribe(listener: (hypothesis: ASRHypothesis) => void): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  private emitHypothesis(hypothesis: ASRHypothesis): void {
    for (const listener of this.listeners) {
      listener(hypothesis);
    }
  }

  async start(options?: ASRStartOptions): Promise<void> {
    if (this.isRunning) return;

    if (typeof window === 'undefined') {
      throw new Error('WebSpeechProvider can only run in a browser environment.');
    }

    if (options?.language) {
      this.language = options.language;
    }

    const SpeechRecognitionConstructor =
      (window as unknown as { SpeechRecognition?: new () => SpeechRecognitionInstance }).SpeechRecognition ||
      (window as unknown as { webkitSpeechRecognition?: new () => SpeechRecognitionInstance }).webkitSpeechRecognition;

    if (!SpeechRecognitionConstructor) {
      throw new Error('Web Speech API is not supported in this browser.');
    }

    try {
      this.recognition = new SpeechRecognitionConstructor();
      this.recognition.continuous = true;
      this.recognition.interimResults = options?.interimResults ?? true;
      this.recognition.lang = this.language;
      this.recognition.maxAlternatives = 1;
      this.sequence = 0;
      this.sessionStartTime = performance.now();
      this.isRunning = true;

      this.recognition.onresult = (event: SpeechRecognitionEvent) => {
        const currentTime = performance.now();
        const startMs = Math.round(currentTime - this.sessionStartTime);

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const res = event.results[i];
          const alt = res[0];
          if (!alt) continue;

          const text = alt.transcript.trim();
          if (!text) continue;

          const isFinal = res.isFinal;
          const confidence = alt.confidence > 0 ? alt.confidence : 0.85;

          const words = text.split(/\s+/).map((w, idx) => ({
            word: w,
            startMs: startMs + idx * 250,
            endMs: startMs + (idx + 1) * 250,
            confidence,
          }));

          const hypothesis: ASRHypothesis = {
            sequence: ++this.sequence,
            text,
            words,
            isFinal,
            startedAtMs: startMs,
            endedAtMs: startMs + words.length * 250,
            confidence,
          };

          this.emitHypothesis(hypothesis);
        }
      };

      this.recognition.onerror = (event: { error: string; message?: string }) => {
        if (event.error === 'no-speech') {
          // Normal silence, don't throw
          return;
        }
        console.warn(`Web Speech API warning: ${event.error}`);
      };

      this.recognition.onend = () => {
        // Auto-restart if session is still actively running
        if (this.isRunning && this.recognition) {
          try {
            this.recognition.start();
          } catch {
            // Already active or terminating
          }
        }
      };

      this.recognition.start();
    } catch (err) {
      this.isRunning = false;
      throw err;
    }
  }

  async stop(): Promise<void> {
    this.isRunning = false;
    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch {
        // ignore
      }
      this.recognition = null;
    }
  }
}

export class MockASRStreamProvider implements ASRProviderPort {
  readonly id = 'mock-asr-fixture-stream';
  private isRunning = false;
  private sequence = 0;
  private timer: NodeJS.Timeout | null = null;
  private scriptTokens: RuntimeToken[];
  private targetWpm: number;
  private listeners: Set<(hypothesis: ASRHypothesis) => void> = new Set();
  private language: string;

  constructor(options?: {
    scriptTokens?: RuntimeToken[];
    targetWpm?: number;
    language?: string;
    enableInterim?: boolean;
    startIndex?: number;
  }) {
    this.scriptTokens = options?.scriptTokens ?? [];
    this.targetWpm = options?.targetWpm ?? 130;
    this.language = options?.language ?? 'uk-UA';
  }

  get capabilities(): ASRCapabilities {
    return {
      supportsWordTimestamps: true,
      supportsConfidence: true,
      supportsInterimResults: true,
      sampleRates: [16000, 48000],
      language: this.language,
    };
  }

  setTokens(tokens: RuntimeToken[]) {
    this.scriptTokens = tokens;
  }

  subscribe(listener: (hypothesis: ASRHypothesis) => void): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  emitHypothesisDirect(hypothesis: ASRHypothesis): void {
    this.emitHypothesis(hypothesis);
  }

  private emitHypothesis(hypothesis: ASRHypothesis): void {
    for (const listener of this.listeners) {
      listener(hypothesis);
    }
  }

  async step(count = 1): Promise<void> {
    const intervalMs = Math.round((60 / this.targetWpm) * 1000);
    const startTime = Date.now();
    for (let i = 0; i < count; i++) {
      if (this.sequence >= this.scriptTokens.length) break;
      const token = this.scriptTokens[this.sequence];
      const elapsed = Date.now() - startTime;
      const seq = ++this.sequence;
      const hyp: ASRHypothesis = {
        sequence: seq,
        text: token.normalizedWord,
        words: [
          {
            word: token.word,
            startMs: elapsed,
            endMs: elapsed + intervalMs,
            confidence: 0.95,
          },
        ],
        isFinal: true,
        startedAtMs: elapsed,
        endedAtMs: elapsed + intervalMs,
        confidence: 0.95,
      };
      this.emitHypothesis(hyp);
    }
  }

  async start(options?: ASRStartOptions): Promise<void> {
    if (this.isRunning) return;
    this.isRunning = true;
    this.sequence = 0;
    if (options?.language) {
      this.language = options.language;
    }

    let currentIndex = 0;
    const intervalMs = Math.round((60 / this.targetWpm) * 1000);
    const startTime = Date.now();

    const emitNext = () => {
      if (!this.isRunning || currentIndex >= this.scriptTokens.length) {
        return;
      }

      const token = this.scriptTokens[currentIndex];
      const elapsed = Date.now() - startTime;
      currentIndex++;

      // First emit interim speculative hypothesis
      const interimHypothesis: ASRHypothesis = {
        sequence: ++this.sequence,
        text: token.normalizedWord,
        words: [
          {
            word: token.word,
            startMs: elapsed,
            endMs: elapsed + intervalMs,
            confidence: 0.88,
          },
        ],
        isFinal: false,
        startedAtMs: elapsed,
        endedAtMs: elapsed + intervalMs,
        confidence: 0.88,
      };
      this.emitHypothesis(interimHypothesis);

      // Shortly after emit final confirmed hypothesis
      setTimeout(() => {
        if (!this.isRunning) return;
        const finalHypothesis: ASRHypothesis = {
          sequence: ++this.sequence,
          text: token.normalizedWord,
          words: [
            {
              word: token.word,
              startMs: elapsed,
              endMs: elapsed + intervalMs,
              confidence: 0.96,
            },
          ],
          isFinal: true,
          startedAtMs: elapsed,
          endedAtMs: elapsed + intervalMs,
          confidence: 0.96,
        };
        this.emitHypothesis(finalHypothesis);
      }, Math.min(100, Math.floor(intervalMs / 2)));

      // Schedule next word, accounting for prosody pause if present
      const pauseExtra = token.prosody?.pauseAfterMs ?? 0;
      this.timer = setTimeout(emitNext, intervalMs + pauseExtra);
    };

    this.timer = setTimeout(emitNext, 300);
  }

  async stop(): Promise<void> {
    this.isRunning = false;
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }
}
