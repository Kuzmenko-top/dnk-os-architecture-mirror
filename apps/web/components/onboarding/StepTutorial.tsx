// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/onboarding/StepTutorial.tsx"
// purpose: "Interactive Canvas Tutorial Step 2 with real-time feedback, action tracking & In-App Canvas Demo integration"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.1.0"
// updated_at: "2026-09-05"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import {
  Plus,
  Wand2,
  Eye,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  RefreshCw,
  Sparkles,
  Layers,
  MonitorPlay
} from 'lucide-react';
import InteractiveCanvasDemo from '../tutorial/InteractiveCanvasDemo';

export interface StepTutorialProps {
  onNext: () => void;
  onBack: () => void;
  onSkip: () => void;
}

export const StepTutorial: React.FC<StepTutorialProps> = ({ onNext, onBack, onSkip }) => {
  // Mode toggle: quick 3-action training vs full interactive 5-step in-app canvas demo
  const [showFullDemo, setShowFullDemo] = useState<boolean>(false);

  // 3 Interactive Actions tracking
  const [createdCanvas, setCreatedCanvas] = useState(false);
  const [generated, setGenerated] = useState(false);
  const [viewedResult, setViewedResult] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  const completedCount = (createdCanvas ? 1 : 0) + (generated ? 1 : 0) + (viewedResult ? 1 : 0);
  const isAllActionsCompleted = completedCount === 3;

  const handleCreateCanvas = () => {
    setCreatedCanvas(true);
    setFeedbackMessage('Чудово! Ви створили полотно');
  };

  const handleGenerate = () => {
    if (!createdCanvas) {
      setFeedbackMessage('Спочатку створіть своє перше полотно!');
      return;
    }
    setGenerated(true);
    setFeedbackMessage('Супер! AI Агент gerych_builder згенерував компонент');
  };

  const handleViewResult = () => {
    if (!generated) {
      setFeedbackMessage('Спочатку натисніть Generate!');
      return;
    }
    setViewedResult(true);
    setFeedbackMessage('Вітаємо! Всі 3 дії інтерактивного туру виконано успішно');
  };

  if (showFullDemo) {
    return (
      <div className="w-full flex flex-col gap-4">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <span className="text-xs font-semibold text-cyan-400 flex items-center gap-2">
            <MonitorPlay className="w-4 h-4" />
            Режим повного інтерактивного туторіалу (5 кроків)
          </span>
          <button
            type="button"
            onClick={() => setShowFullDemo(false)}
            className="text-xs text-gray-400 hover:text-white px-2.5 py-1 rounded-lg bg-white/5 border border-white/10"
          >
            Повернутися до спрощеного тренінгу
          </button>
        </div>
        <InteractiveCanvasDemo
          onComplete={() => {
            onNext();
          }}
          onExit={() => setShowFullDemo(false)}
        />
      </div>
    );
  }

  return (
    <section
      aria-label="Інтерактивний туторіал полотна Canvas"
      className="flex flex-col py-4 px-3 max-w-2xl mx-auto w-full"
    >
      <div className="text-center mb-5">
        <div className="flex items-center justify-center gap-2 mb-2">
          <button
            type="button"
            onClick={() => setShowFullDemo(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs font-semibold hover:bg-cyan-500/20 transition-all"
          >
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>Запустити інтерактивне демо полотна (5 кроків) →</span>
          </button>
        </div>
        <h2 className="text-2xl font-bold text-white mb-2 flex items-center justify-center gap-2">
          <Layers className="w-6 h-6 text-cyan-400" aria-hidden="true" />
          Інтерактивний Canvas: Практичний тренінг
        </h2>
        <p className="text-sm text-gray-300">
          Виконайте 3 прості дії у віртуальному демо-полотні, щоб зрозуміти механіку взаємодії з агентами.
        </p>
      </div>

      {/* Progress tracking badge: X з 3 дій виконано */}
      <div className="flex items-center justify-between bg-white/[0.03] border border-white/10 rounded-xl px-4 py-2.5 mb-4">
        <span className="text-xs font-medium text-gray-300">Прогрес туторіалу:</span>
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-cyan-400">{completedCount} з 3 дій виконано</span>
          <div className="w-24 h-2 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-cyan-400 to-blue-500 transition-all duration-300"
              style={{ width: `${(completedCount / 3) * 100}%` }}
              role="progressbar"
              aria-valuenow={completedCount}
              aria-valuemin={0}
              aria-valuemax={3}
            />
          </div>
        </div>
      </div>

      {/* Interactive Canvas Simulator Sandbox */}
      <div className="bg-[#0b0f19] border border-white/15 rounded-2xl p-5 mb-4 relative overflow-hidden shadow-2xl">
        <div className="flex items-center justify-between border-b border-white/10 pb-3 mb-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500/80" />
            <div className="w-3 h-3 rounded-full bg-amber-500/80" />
            <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
            <span className="text-xs text-gray-400 ml-2 font-mono">canvas-preview://workspace-demo</span>
          </div>
          {isAllActionsCompleted && (
            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Готово до наступного кроку
            </span>
          )}
        </div>

        {/* Action Steps Interactive Buttons */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
          {/* Action 1 */}
          <button
            onClick={handleCreateCanvas}
            type="button"
            className={`p-3.5 rounded-xl border text-left transition-all flex flex-col justify-between ${
              createdCanvas
                ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-300'
                : 'bg-white/[0.04] hover:bg-white/[0.08] border-white/15 text-white active:scale-98'
            }`}
          >
            <div className="flex items-center justify-between w-full mb-2">
              <span className="text-[11px] font-mono text-gray-400 uppercase">Дія 1</span>
              {createdCanvas ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              ) : (
                <Plus className="w-4 h-4 text-cyan-400" />
              )}
            </div>
            <div>
              <span className="text-xs font-semibold block mb-0.5">Створіть своє перше полотно</span>
              <span className="text-[10px] text-gray-400">Натисніть для ініціалізації полотна</span>
            </div>
          </button>

          {/* Action 2 */}
          <button
            onClick={handleGenerate}
            type="button"
            className={`p-3.5 rounded-xl border text-left transition-all flex flex-col justify-between ${
              generated
                ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-300'
                : 'bg-white/[0.04] hover:bg-white/[0.08] border-white/15 text-white active:scale-98'
            }`}
          >
            <div className="flex items-center justify-between w-full mb-2">
              <span className="text-[11px] font-mono text-gray-400 uppercase">Дія 2</span>
              {generated ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              ) : (
                <Wand2 className="w-4 h-4 text-purple-400" />
              )}
            </div>
            <div>
              <span className="text-xs font-semibold block mb-0.5">Generate</span>
              <span className="text-[10px] text-gray-400">Запустіть генерацію коду агентом</span>
            </div>
          </button>

          {/* Action 3 */}
          <button
            onClick={handleViewResult}
            type="button"
            className={`p-3.5 rounded-xl border text-left transition-all flex flex-col justify-between ${
              viewedResult
                ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-300'
                : 'bg-white/[0.04] hover:bg-white/[0.08] border-white/15 text-white active:scale-98'
            }`}
          >
            <div className="flex items-center justify-between w-full mb-2">
              <span className="text-[11px] font-mono text-gray-400 uppercase">Дія 3</span>
              {viewedResult ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              ) : (
                <Eye className="w-4 h-4 text-blue-400" />
              )}
            </div>
            <div>
              <span className="text-xs font-semibold block mb-0.5">Подивіться результат</span>
              <span className="text-[10px] text-gray-400">Оцініть інтерактивний рендеринг</span>
            </div>
          </button>
        </div>

        {/* Real-time Feedback Notification Banner */}
        {feedbackMessage && (
          <div
            role="status"
            aria-live="polite"
            className="mb-4 p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs flex items-center gap-2 animate-fade-in"
          >
            <Sparkles className="w-4 h-4 text-cyan-400 flex-shrink-0" />
            <span className="font-medium">{feedbackMessage}</span>
          </div>
        )}

        {/* Canvas Display Viewport Simulation */}
        <div className="border border-dashed border-white/20 bg-black/40 rounded-xl p-4 min-h-[140px] flex flex-col items-center justify-center text-center">
          {!createdCanvas ? (
            <div className="flex flex-col items-center">
              <span className="text-xs text-gray-500 mb-1">Полотно очікує ініціалізації</span>
              <p className="text-[11px] text-gray-400">Клацніть "Створіть своє перше полотно" вище для початку.</p>
            </div>
          ) : !generated ? (
            <div className="flex flex-col items-center">
              <span className="text-xs text-cyan-300 font-mono mb-1">Canvas initialized: workspace_v1</span>
              <p className="text-[11px] text-gray-400">Вузол створено. Натисніть кнопку Generate для запуску AI агента.</p>
            </div>
          ) : !viewedResult ? (
            <div className="flex flex-col items-center">
              <span className="inline-flex items-center gap-1.5 text-xs text-purple-300 font-mono mb-1">
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-purple-400" />
                Синтез завершено: 120 рядків React коду
              </span>
              <p className="text-[11px] text-gray-400">Натисніть "Подивіться результат" для перегляду згенерованого інтерфейсу.</p>
            </div>
          ) : (
            <div className="w-full flex flex-col items-center bg-white/[0.02] p-3 rounded-lg border border-emerald-500/20">
              <span className="text-xs font-semibold text-emerald-400 mb-1">✨ Результат згенеровано успішно!</span>
              <p className="text-[11px] text-gray-300">
                Компонент розміщено на Canvas. Ви можете масштабувати, редагувати код або запустити аудит безпеки.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Navigation Footer */}
      <div className="flex items-center justify-between w-full pt-2">
        <button
          onClick={onBack}
          type="button"
          className="px-4 py-2.5 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] text-gray-300 text-xs font-medium flex items-center gap-1.5 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Назад</span>
        </button>

        <div className="flex items-center gap-2">
          <button
            onClick={onSkip}
            type="button"
            className="px-3 py-2 text-gray-400 hover:text-gray-200 text-xs transition-colors"
          >
            Пропустити
          </button>
          <button
            onClick={onNext}
            type="button"
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-cyan-500/20 transition-all"
          >
            <span>Далі</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </section>
  );
};

export default StepTutorial;
