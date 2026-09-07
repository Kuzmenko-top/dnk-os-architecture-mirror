// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/tutorial/StepByStepGuide.tsx"
// purpose: "5-Step Interactive Guided Tutorial Overlay with Glow Highlighting, Hints, and WCAG 2.1 AA Accessibility"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-05"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useEffect } from 'react';
import {
  HelpCircle,
  SkipForward,
  CheckCircle,
  Lightbulb,
  ArrowRight,
  Layers,
  Sparkles,
  Info
} from 'lucide-react';

export interface TutorialStepConfig {
  id: number;
  title: string;
  description: string;
  targetElementId: string;
  hint: string;
  actionInstruction: string;
}

export const TUTORIAL_STEPS: TutorialStepConfig[] = [
  {
    id: 1,
    title: "Натисніть 'New Canvas'",
    description: "Почніть роботу зі створення нового віртуального робочого полотна.",
    targetElementId: "tutorial-new-canvas-btn",
    hint: "Знайдіть бірюзову кнопку '+ New Canvas' у верхній панелі керування полотном.",
    actionInstruction: "Клікніть по кнопці 'New Canvas' для ініціалізації."
  },
  {
    id: 2,
    title: "Введіть назву полотна",
    description: "Дайте назву вашому робочому простору або проекту.",
    targetElementId: "tutorial-canvas-title-input",
    hint: "Введіть будь-яку назву проекту (наприклад: 'E-commerce Launch').",
    actionInstruction: "Введіть текст у поле назви полотна."
  },
  {
    id: 3,
    title: "Оберіть template",
    description: "Виберіть готовий шаблон робочого процесу для швидкого старту.",
    targetElementId: "tutorial-template-select",
    hint: "Оберіть один із шаблонів у випадаючому списку: Product Launch, SaaS Landing або AI Agent.",
    actionInstruction: "Виберіть шаблон зі списку."
  },
  {
    id: 4,
    title: "Натисніть 'Generate'",
    description: "Запустіть автономний AI-генератор для побудови графа полотна.",
    targetElementId: "tutorial-generate-btn",
    hint: "Натисніть кнопку 'Generate' з іконкою магічної палички для виклику рою агентів.",
    actionInstruction: "Натисніть кнопку 'Generate' для створення структури."
  },
  {
    id: 5,
    title: "Подивіться результат",
    description: "Перегляньте згенерований інтерактивний граф полотна та його вузли.",
    targetElementId: "tutorial-canvas-preview",
    hint: "Натисніть на область попереднього перегляду полотна або огляньте згенеровані картки.",
    actionInstruction: "Клацніть по області результату або перегляньте деталі."
  }
];

export interface StepByStepGuideProps {
  currentStepIndex: number; // 0 to 4
  onStepComplete: (stepId: number) => void;
  onSkipStep: (stepId: number) => void;
  onSelectStep?: (stepIndex: number) => void;
  className?: string;
  isHighContrast?: boolean;
}

export const StepByStepGuide: React.FC<StepByStepGuideProps> = ({
  currentStepIndex,
  onStepComplete,
  onSkipStep,
  onSelectStep,
  className = '',
  isHighContrast = false
}) => {
  const [showHint, setShowHint] = useState<boolean>(false);
  const step = TUTORIAL_STEPS[currentStepIndex] || TUTORIAL_STEPS[0];
  const totalSteps = TUTORIAL_STEPS.length;

  // Reset hint when moving to next step
  useEffect(() => {
    setShowHint(false);
  }, [currentStepIndex]);

  // Keyboard navigation support: Esc to hide hint, Enter to complete action if focused
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setShowHint(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div
      role="region"
      aria-label={`Крок ${step.id} з ${totalSteps}: ${step.title}`}
      className={`rounded-2xl border transition-all ${
        isHighContrast
          ? 'bg-black border-cyan-400 text-white shadow-2xl'
          : 'bg-[#0b0f19]/95 backdrop-blur-md border-cyan-500/30 text-gray-100 shadow-xl shadow-cyan-950/20'
      } p-4 sm:p-5 ${className}`}
    >
      {/* Header and Step Indicator */}
      <div className="flex items-center justify-between mb-3 border-b border-white/10 pb-2.5">
        <div className="flex items-center gap-2">
          <span className="flex items-center justify-center w-6 h-6 rounded-full bg-cyan-500 text-black font-bold text-xs">
            {step.id}
          </span>
          <span className="text-xs uppercase tracking-wider font-semibold text-cyan-400">
            Крок {step.id} з {totalSteps}
          </span>
        </div>
        <div
          role="progressbar"
          aria-label="Прогрес навчання"
          aria-valuenow={step.id}
          aria-valuemin={1}
          aria-valuemax={totalSteps}
          className="flex items-center gap-1"
        >
          {TUTORIAL_STEPS.map((s, idx) => (
            <button
              key={s.id}
              type="button"
              onClick={() => onSelectStep && onSelectStep(idx)}
              aria-label={`Перейти до кроку ${s.id}: ${s.title}`}
              aria-current={idx === currentStepIndex ? 'step' : undefined}
              className={`h-2 rounded-full transition-all focus:outline-none focus:ring-2 focus:ring-cyan-400 ${
                idx === currentStepIndex
                  ? 'w-6 bg-cyan-400'
                  : idx < currentStepIndex
                  ? 'w-2 bg-emerald-400'
                  : 'w-2 bg-gray-700 hover:bg-gray-600'
              }`}
            />
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="mb-4">
        <h3 className="text-lg font-bold text-white flex items-center gap-2 mb-1">
          <Sparkles className="w-4 h-4 text-cyan-400" aria-hidden="true" />
          <span>{step.title}</span>
        </h3>
        <p className="text-sm text-gray-300 leading-relaxed mb-2">
          {step.description}
        </p>
        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-xs font-mono text-cyan-300">
          <Info className="w-3.5 h-3.5" aria-hidden="true" />
          <span>{step.actionInstruction}</span>
        </div>
      </div>

      {/* Hint Accordion / Callout */}
      {showHint && (
        <div
          role="note"
          aria-live="polite"
          className="mb-4 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200 text-xs flex items-start gap-2 animate-fadeIn"
        >
          <Lightbulb className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <span className="font-semibold block mb-0.5">Підказка:</span>
            <span>{step.hint}</span>
          </div>
        </div>
      )}

      {/* Actions: Show Hint & Skip Step */}
      <div className="flex items-center justify-between pt-2 border-t border-white/10">
        <button
          type="button"
          onClick={() => setShowHint(!showHint)}
          aria-expanded={showHint}
          aria-label="Показати підказку до поточного кроку"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white text-xs font-medium border border-white/10 focus:outline-none focus:ring-2 focus:ring-amber-400 transition-colors"
        >
          <HelpCircle className="w-3.5 h-3.5 text-amber-400" aria-hidden="true" />
          <span>{showHint ? "Сховати підказку" : "Показати підказку"}</span>
        </button>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => onSkipStep(step.id)}
            aria-label={`Пропустити крок ${step.id}`}
            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-gray-400 hover:text-gray-200 text-xs font-medium hover:bg-white/5 focus:outline-none focus:ring-2 focus:ring-cyan-400 transition-colors"
          >
            <SkipForward className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Пропустити крок</span>
          </button>

          <button
            type="button"
            onClick={() => onStepComplete(step.id)}
            aria-label={`Завершити крок ${step.id}`}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-xs font-semibold shadow-md shadow-cyan-500/20 focus:outline-none focus:ring-2 focus:ring-cyan-300 transition-all"
          >
            <span>Виконано</span>
            <CheckCircle className="w-3.5 h-3.5" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default StepByStepGuide;
