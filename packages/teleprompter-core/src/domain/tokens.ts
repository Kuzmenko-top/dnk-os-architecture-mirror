/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/teleprompter-core/src/domain/tokens.ts"
# purpose: "Runtime Tokens, Token Status Types, and Script Flattening Service."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { ScriptDocument, ProsodyDocument, ProsodyToken } from '@dnk/video-audit-core';
import { DefaultTextNormalizer, TextNormalizerPort } from '../ports/normalizer.js';
import { ContractVersionMismatchError } from '../errors/errors.js';

export type TokenStatus =
  | 'upcoming'
  | 'speculative'
  | 'confirmed'
  | 'completed'
  | 'skipped'
  | 'manual_reset';

export interface RuntimeProsodyCue {
  emphasis?: 'none' | 'punch' | 'soft' | 'whisper' | 'stretched' | 'hold';
  pitchShift?: 'normal' | 'high' | 'low';
  pauseAfterMs?: number;
  gesture?: string;
  sourceProsodyId?: string;
}

export interface RuntimeToken {
  index: number;
  word: string;
  normalizedWord: string;
  sceneId: string;
  sceneRole?: string;
  paragraphId: string;
  speakerRole?: string;
  status: TokenStatus;
  prosody?: RuntimeProsodyCue;
  estimatedStartMs: number;
  estimatedEndMs: number;
  actualStartMs?: number;
  actualEndMs?: number;
  matchedHypothesisSeq?: number;
}

export interface FlattenScriptOptions {
  targetWpm?: number;
  normalizer?: TextNormalizerPort;
}

export class ScriptFlatteningService {
  private readonly normalizer: TextNormalizerPort;

  constructor(normalizer?: TextNormalizerPort) {
    this.normalizer = normalizer || new DefaultTextNormalizer();
  }

  /**
   * Transforms hierarchical ScriptDocument and optional ProsodyDocument into
   * a flat sequential array of RuntimeToken objects with timing estimates.
   */
  flatten(
    script: ScriptDocument,
    prosody?: ProsodyDocument,
    options?: FlattenScriptOptions
  ): RuntimeToken[] {
    if (script.schemaVersion !== 'script.v1') {
      throw new ContractVersionMismatchError(
        'script.v1',
        script.schemaVersion,
        'ScriptDocument'
      );
    }

    if (prosody && prosody.schemaVersion !== 'prosody.v1') {
      throw new ContractVersionMismatchError(
        'prosody.v1',
        prosody.schemaVersion,
        'ProsodyDocument'
      );
    }

    const targetWpm =
      options?.targetWpm || prosody?.globalPacing?.targetWpm || 140;
    const msPerWord = Math.max(100, Math.round((60 / targetWpm) * 1000));

    // Build lookup maps for prosody tokens:
    // Primary key: sceneId + paragraphId + word (case-insensitive)
    // Secondary queue: per sceneId + paragraphId
    const prosodyMap = new Map<string, ProsodyToken[]>();
    if (prosody?.tokens) {
      for (const pToken of prosody.tokens) {
        const key = `${pToken.sceneId}::${pToken.paragraphId}::${this.normalizer.normalize(pToken.word)}`;
        const existing = prosodyMap.get(key) || [];
        existing.push(pToken);
        prosodyMap.set(key, existing);
      }
    }

    const tokens: RuntimeToken[] = [];
    let currentTimelineMs = 0;
    let tokenIndex = 0;

    for (const scene of script.scenes) {
      for (const paragraph of scene.paragraphs) {
        const words = paragraph.text
          .trim()
          .split(/\s+/)
          .filter((w: string) => w.length > 0);

        for (const rawWord of words) {
          const normWord = this.normalizer.normalize(rawWord);
          const lookupKey = `${scene.id}::${paragraph.id}::${normWord}`;
          const matchingProsodies = prosodyMap.get(lookupKey);
          let matchedProsody: ProsodyToken | undefined;

          if (matchingProsodies && matchingProsodies.length > 0) {
            matchedProsody = matchingProsodies.shift();
          }

          const pauseAfterMs = matchedProsody?.pauseAfterMs || 0;
          const holdBonusMs =
            matchedProsody?.emphasis === 'stretched' ? 300 : 0;
          const wordDurationMs = msPerWord + holdBonusMs;

          const startMs = currentTimelineMs;
          const endMs = startMs + wordDurationMs;

          let prosodyCue: RuntimeProsodyCue | undefined;
          if (matchedProsody) {
            prosodyCue = {
              emphasis: matchedProsody.emphasis,
              pitchShift: matchedProsody.pitchShift,
              pauseAfterMs: matchedProsody.pauseAfterMs,
              gesture: matchedProsody.gesture,
              sourceProsodyId: matchedProsody.id,
            };
          }

          tokens.push({
            index: tokenIndex++,
            word: rawWord,
            normalizedWord: normWord,
            sceneId: scene.id,
            sceneRole: scene.role,
            paragraphId: paragraph.id,
            speakerRole: paragraph.speakerRole,
            status: 'upcoming',
            prosody: prosodyCue,
            estimatedStartMs: startMs,
            estimatedEndMs: endMs,
          });

          currentTimelineMs = endMs + pauseAfterMs;
        }
      }
    }

    return tokens;
  }
}
