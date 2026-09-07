/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/adaptation/domain/transformers/prosody-transformer.ts"
# purpose: "Transforms ScriptDocument into Teleprompter-Ready ProsodyDocument (prosody.v1)."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import {
  ProsodyDocument,
  ProsodyToken,
  ProsodyEmphasis,
  ProsodyPitch,
  ProsodyGesture,
} from '../../../schemas/prosody.js';
import { ScriptDocument } from '../../../schemas/script.js';

export class ProsodyTransformer {
  /**
   * Transforms a script into teleprompter-ready tokens with vocal emphasis,
   * pitch inflection, pause durations, and physical gesture cues.
   */
  public transform(script: ScriptDocument, targetDurationMs?: number): ProsodyDocument {
    const tokens: ProsodyToken[] = [];
    let wordIndex = 0;

    const technicalPunchWords = new Set([
      'aisi',
      '304',
      'нержавійка',
      'нержавіючої',
      'димогенератор',
      'конденсат',
      'конденсатовідвідник',
      'конвекція',
      'конвекції',
      'дефлектор',
      'дефлекторний',
      'pid',
      'термоконтролер',
      'термощуп',
      'холодне',
      'гаряче',
      'тріска',
      'якість',
      'смол',
      'гіркоти',
      'помилка',
      'увага',
      'reburn',
    ]);

    const estimatedTotalMs = targetDurationMs ?? script.estimatedDurationMs ?? 30000;

    // Count all words first to compute pacing
    const totalWords = script.scenes
      .flatMap(s => s.paragraphs.flatMap(p => p.text.split(/\s+/).filter(Boolean)))
      .length;

    const targetWpm = totalWords > 0 && estimatedTotalMs > 0
      ? Math.round((totalWords / (estimatedTotalMs / 1000)) * 60)
      : 140;

    for (const scene of script.scenes) {
      const isHookScene = scene.role === 'hook';
      const isCtaScene = scene.role === 'call_to_action';

      for (const para of scene.paragraphs) {
        const rawWords = para.text.split(/\s+/).filter(Boolean);

        for (let i = 0; i < rawWords.length; i++) {
          const raw = rawWords[i];
          const cleanWord = raw.toLowerCase().replace(/[^a-zа-яіїєґ0-9]/g, '');

          let emphasis: ProsodyEmphasis = 'none';
          let pitchShift: ProsodyPitch = 'normal';
          let pauseAfterMs = 0;
          let gesture: ProsodyGesture = 'none';

          // Technical Punch Word
          if (technicalPunchWords.has(cleanWord)) {
            emphasis = 'punch';
          }

          // Hook scene prosody
          if (isHookScene && i === 0) {
            pitchShift = 'high';
            emphasis = 'punch';
            gesture = 'finger_point';
          }

          // Question mark inflection
          if (raw.endsWith('?')) {
            pitchShift = 'high';
            pauseAfterMs = 500;
            gesture = 'lean_forward';
          } else if (raw.endsWith('!') || raw.endsWith('.')) {
            pitchShift = 'low';
            pauseAfterMs = 400;
            if (isCtaScene && i === rawWords.length - 1) {
              gesture = 'palms_up';
            } else if (i === rawWords.length - 1) {
              gesture = 'head_nod';
            }
          } else if (raw.endsWith(':') || raw.endsWith(';')) {
            pauseAfterMs = 300;
          }

          tokens.push({
            id: `tok-${wordIndex + 1}`,
            word: raw,
            sceneId: scene.id,
            paragraphId: para.id,
            emphasis,
            pitchShift,
            pauseAfterMs,
            gesture,
          });

          wordIndex++;
        }
      }
    }

    return {
      schemaVersion: 'prosody.v1',
      scriptId: script.id,
      globalPacing: {
        targetWpm,
        targetDurationMs: estimatedTotalMs,
      },
      tokens,
    };
  }
}
