import { describe, it, expect } from 'vitest';
import { ScriptFlatteningService } from '../../src/domain/tokens.js';
import { ContractVersionMismatchError } from '../../src/errors/errors.js';
import { ScriptDocument, ProsodyDocument } from '@dnk/video-audit-core';

describe('ScriptFlatteningService', () => {
  const sampleScript: ScriptDocument = {
    schemaVersion: 'script.v1',
    id: 'test-script-1',
    language: 'uk',
    title: 'Тестовий сценарій',
    estimatedDurationMs: 15000,
    scenes: [
      {
        id: 'scene-1',
        title: 'Вступ',
        role: 'hook',
        targetTimeRange: { startMs: 0, endMs: 5000 },
        paragraphs: [
          {
            id: 'p-1',
            text: 'Привіт, це тестове відео про штучний інтелект.',
            speakerRole: 'main_speaker',
            estimatedDurationMs: 5000,
          },
        ],
      },
    ],
  };

  const sampleProsody: ProsodyDocument = {
    schemaVersion: 'prosody.v1',
    scriptId: 'test-script-1',
    globalPacing: {
      targetWpm: 120,
      targetDurationMs: 15000,
    },
    tokens: [
      {
        id: 'pt-1',
        word: 'Привіт',
        sceneId: 'scene-1',
        paragraphId: 'p-1',
        emphasis: 'punch',
        pitchShift: 'high',
        pauseAfterMs: 400,
        gesture: 'wave',
      },
      {
        id: 'pt-2',
        word: 'інтелект',
        sceneId: 'scene-1',
        paragraphId: 'p-1',
        emphasis: 'hold',
        pitchShift: 'normal',
        pauseAfterMs: 200,
      },
    ],
  };

  it('should flatten script scenes and paragraphs into runtime tokens', () => {
    const service = new ScriptFlatteningService();
    const tokens = service.flatten(sampleScript, sampleProsody);

    expect(tokens.length).toBe(7);
    expect(tokens[0].word).toBe('Привіт,');
    expect(tokens[0].normalizedWord).toBe('привіт');
    expect(tokens[0].prosody?.emphasis).toBe('punch');
    expect(tokens[0].prosody?.pauseAfterMs).toBe(400);
    expect(tokens[0].prosody?.gesture).toBe('wave');

    const lastToken = tokens[tokens.length - 1];
    expect(lastToken.normalizedWord).toBe('інтелект');
    expect(lastToken.prosody?.emphasis).toBe('hold');
  });

  it('should throw ContractVersionMismatchError for invalid schema versions', () => {
    const service = new ScriptFlatteningService();
    const badScript = { ...sampleScript, schemaVersion: 'script.v2' as any };

    expect(() => service.flatten(badScript)).toThrow(
      ContractVersionMismatchError
    );
  });
});
