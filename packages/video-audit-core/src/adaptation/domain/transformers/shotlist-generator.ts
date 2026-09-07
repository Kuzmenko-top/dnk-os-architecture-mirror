/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/adaptation/domain/transformers/shotlist-generator.ts"
# purpose: "Generates Video ShotList (shot-list.v1) from Adapted Script Document."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { ShotList, ShotInstruction } from '../../../schemas/shotlist.js';
import { ScriptDocument } from '../../../schemas/script.js';

export class ShotListGenerator {
  public generate(script: ScriptDocument): ShotList {
    const shots: ShotInstruction[] = [];
    let shotIdx = 1;

    for (const scene of script.scenes) {
      let shotType: ShotInstruction['shotType'] = 'medium_shot';
      let visualPrompt = '';
      let bRollKeywords: string[] = [];
      let cameraAngle = 'eye_level';

      switch (scene.role) {
        case 'hook':
          shotType = 'close_up';
          visualPrompt = 'Енергійний ведучий крупним планом вказує пальцем у камеру або тримає розрізане соковите м’ясо.';
          bRollKeywords = ['bbq', 'juicy meat', 'smoke', 'close-up'];
          cameraAngle = 'dynamic_low_angle';
          break;

        case 'problem_statement':
          shotType = 'b_roll';
          visualPrompt = 'Кадри типових помилок: гіркий темний конденсат на стінках кустарної коптильні, пересушений продукт.';
          bRollKeywords = ['tar', 'bitter smoke', 'condensate', 'ruined meat'];
          cameraAngle = 'overhead_macro';
          break;

        case 'core_value':
        case 'demonstration':
          shotType = 'close_up';
          visualPrompt = 'Макро-зйомка аргонних швів нержавіючої сталі AISI 304, робота димогенератора ReBurn та конвекції.';
          bRollKeywords = ['stainless steel', 'aisi 304', 'tig weld', 'smoke generator', 'convection'];
          cameraAngle = 'close_dolly';
          break;

        case 'call_to_action':
          shotType = 'medium_shot';
          visualPrompt = 'Ведучий біля готової коптильної установки ReBurn посміхається і показує жест у бік контактів / директу.';
          bRollKeywords = ['turnkey smoker', 'satisfied craftsman', 'call to action'];
          cameraAngle = 'eye_level';
          break;

        default:
          shotType = 'medium_shot';
          visualPrompt = `Демонстрація робочого процесу: ${scene.title}.`;
          bRollKeywords = ['craft smoking', 'commercial kitchen'];
          cameraAngle = 'eye_level';
          break;
      }

      const sceneDuration = scene.paragraphs.reduce(
        (acc, p) => acc + (p.estimatedDurationMs ?? 3000),
        0
      );

      shots.push({
        id: `shot-${shotIdx++}`,
        sceneId: scene.id,
        shotType,
        visualPrompt,
        estimatedDurationMs: sceneDuration > 0 ? sceneDuration : 4000,
        bRollKeywords,
        cameraAngle,
      });
    }

    return {
      schemaVersion: 'shot-list.v1',
      scriptId: script.id,
      shots,
    };
  }
}
