// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/tutorial/InteractiveCanvasDemo.tsx"
// purpose: "Interactive In-App Canvas Tutorial Demo with Mock Canvas, Step-by-Step Glow, Real-time Feedback, and Achievement Badges"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-05"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Plus,
  Wand2,
  Eye,
  CheckCircle2,
  RefreshCw,
  Sparkles,
  Layers,
  Layout,
  Play,
  RotateCcw,
  Sliders,
  Award,
  ArrowRight
} from 'lucide-react';
import StepByStepGuide, { TUTORIAL_STEPS } from './StepByStepGuide';
import RealTimeFeedback, { ToastMessage } from './RealTimeFeedback';
import AchievementBadges, { INITIAL_BADGES, AchievementBadge } from './AchievementBadges';

export interface InteractiveCanvasDemoProps {
  onComplete?: () => void;
  onExit?: () => void;
  className?: string;
  autoStart?: boolean;
}

// LocalStorage Keys
const STORAGE_TUTORIAL_COMPLETED = 'tutorial_completed';
const STORAGE_TUTORIAL_PROGRESS = 'tutorial_progress';
const STORAGE_TUTORIAL_CURRENT_STEP = 'tutorial_current_step';
const STORAGE_ACHIEVEMENTS = 'dnk_tutorial_achievements';

// Mock Canvas State
interface MockCanvasNode {
  id: string;
  title: string;
  type: 'agent' | 'model' | 'output' | 'input';
  x: number;
  y: number;
  status: 'idle' | 'running' | 'success';
}

const INITIAL_MOCK_NODES: MockCanvasNode[] = [
  { id: 'node-1', title: 'Input Prompt', type: 'input', x: 20, y: 30, status: 'success' },
  { id: 'node-2', title: 'Gerych Planner', type: 'agent', x: 180, y: 30, status: 'running' },
  { id: 'node-3', title: 'Builder Worker', type: 'agent', x: 340, y: 30, status: 'idle' },
  { id: 'node-4', title: 'Auditor Gate', type: 'agent', x: 500, y: 30, status: 'idle' },
];

export const InteractiveCanvasDemo: React.FC<InteractiveCanvasDemoProps> = ({
  onComplete,
  onExit,
  className = '',
  autoStart = true
}) => {
  // Step index: 0 = Step 1, 1 = Step 2, 2 = Step 3, 3 = Step 4, 4 = Step 5
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [toast, setToast] = useState<ToastMessage | null>(null);
  const [showConfetti, setShowConfetti] = useState<boolean>(false);
  const [soundEnabled, setSoundEnabled] = useState<boolean>(false);
  const [badges, setBadges] = useState<AchievementBadge[]>(INITIAL_BADGES);
  const [canvasCreated, setCanvasCreated] = useState<boolean>(false);
  const [canvasTitle, setCanvasTitle] = useState<string>('My First Project');
  const [selectedTemplate, setSelectedTemplate] = useState<string>('e-commerce');
  const [isGenerated, setIsGenerated] = useState<boolean>(false);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [previewClicked, setPreviewClicked] = useState<boolean>(false);
  const [createdCanvasesCount, setCreatedCanvasesCount] = useState<number>(0);
  const [startTime] = useState<number>(Date.now());
  const [isHighContrast, setIsHighContrast] = useState<boolean>(false);
  const [reducedMotion, setReducedMotion] = useState<boolean>(false);

  // Analytics event logger helper
  const logAnalytics = (event: string, properties?: Record<string, unknown>) => {
    try {
      if (typeof window !== 'undefined') {
        const payload = {
          event,
          timestamp: new Date().toISOString(),
          step: currentStepIndex + 1,
          ...properties
        };
        // Emit custom DOM event for analytics listeners
        window.dispatchEvent(new CustomEvent('dnk_analytics_event', { detail: payload }));
        // Also log to console in dev mode
        if (process.env.NODE_ENV !== 'production') {
          console.log(`[Tutorial Analytics] ${event}`, payload);
        }
      }
    } catch {
      // Ignore logging failures
    }
  };

  // Restore state from LocalStorage on mount
  useEffect(() => {
    try {
      if (typeof window !== 'undefined') {
        const savedCompleted = localStorage.getItem(STORAGE_TUTORIAL_COMPLETED);
        const savedProgress = localStorage.getItem(STORAGE_TUTORIAL_PROGRESS);
        const savedStep = localStorage.getItem(STORAGE_TUTORIAL_CURRENT_STEP);
        const savedBadges = localStorage.getItem(STORAGE_ACHIEVEMENTS);

        if (savedStep) {
          const parsedStep = parseInt(savedStep, 10);
          if (!isNaN(parsedStep) && parsedStep >= 0 && parsedStep < TUTORIAL_STEPS.length) {
            setCurrentStepIndex(parsedStep);
          }
        }
        if (savedProgress) {
          const parsed = JSON.parse(savedProgress);
          if (Array.isArray(parsed)) setCompletedSteps(parsed);
        }
        if (savedBadges) {
          const parsedB = JSON.parse(savedBadges);
          if (Array.isArray(parsedB)) setBadges(parsedB);
        }

        // Fire tutorial_started event
        logAnalytics('tutorial_started', { initial_step: savedStep || 0 });
      }
    } catch {
      // LocalStorage access restricted or unavailable
    }

    return () => {
      // When unmounting before completion, log abandonment if not completed
      const isDone = localStorage.getItem(STORAGE_TUTORIAL_COMPLETED) === 'true';
      if (!isDone) {
        logAnalytics('tutorial_abandoned', { last_step: currentStepIndex + 1 });
      }
    };
  }, []);

  // Unlock badge helper
  const unlockBadge = (badgeId: string) => {
    setBadges(prev => {
      const updated = prev.map(b => {
        if (b.id === badgeId && !b.isUnlocked) {
          return {
            ...b,
            isUnlocked: true,
            unlockedAt: new Date().toISOString()
          };
        }
        return b;
      });
      try {
        localStorage.setItem(STORAGE_ACHIEVEMENTS, JSON.stringify(updated));
      } catch {}
      return updated;
    });
  };

  // Step Advancement and Persistence
  const markStepDone = (stepId: number, autoAdvance: boolean = true) => {
    const updatedCompleted = Array.from(new Set([...completedSteps, stepId]));
    setCompletedSteps(updatedCompleted);

    logAnalytics('tutorial_step_completed', {
      step_id: stepId,
      step_title: TUTORIAL_STEPS[stepId - 1]?.title
    });

    try {
      localStorage.setItem(STORAGE_TUTORIAL_PROGRESS, JSON.stringify(updatedCompleted));
    } catch {}

    if (autoAdvance && stepId < TUTORIAL_STEPS.length) {
      const nextIndex = stepId; // stepId is 1-based, index is 0-based
      setCurrentStepIndex(nextIndex);
      try {
        localStorage.setItem(STORAGE_TUTORIAL_CURRENT_STEP, String(nextIndex));
      } catch {}
    } else if (stepId === TUTORIAL_STEPS.length) {
      finalizeTutorial();
    }
  };

  // Finalize Tutorial Flow
  const finalizeTutorial = () => {
    setShowConfetti(true);
    setToast({
      id: 'completion-toast',
      type: 'success',
      message: 'Вітаємо! Ви успішно пройшли всі 5 кроків інтерактивного туторіалу! 🎉',
      durationMs: 5000
    });

    // Unlock badges
    unlockBadge('onboarding-complete');
    const elapsedMinutes = (Date.now() - startTime) / (1000 * 60);
    if (elapsedMinutes < 5) {
      unlockBadge('quick-learner');
    }

    try {
      localStorage.setItem(STORAGE_TUTORIAL_COMPLETED, 'true');
      localStorage.setItem(STORAGE_TUTORIAL_CURRENT_STEP, String(TUTORIAL_STEPS.length - 1));
    } catch {}

    logAnalytics('tutorial_completed', { elapsed_minutes: elapsedMinutes.toFixed(2) });

    if (onComplete) {
      setTimeout(() => {
        onComplete();
      }, 1500);
    }
  };

  // Action 1: Create Canvas
  const handleNewCanvasClick = () => {
    setCanvasCreated(true);
    const newCount = createdCanvasesCount + 1;
    setCreatedCanvasesCount(newCount);

    unlockBadge('first-canvas');
    if (newCount >= 3) {
      unlockBadge('creative-mind');
    }

    setToast({
      id: 'action-1-toast',
      type: 'success',
      message: 'Чудово! Ви створили полотно ✅'
    });

    markStepDone(1, true);
  };

  // Action 2: Title input change / submit
  const handleTitleChange = (val: string) => {
    setCanvasTitle(val);
  };

  const handleTitleSubmit = () => {
    if (!canvasTitle.trim()) {
      setToast({
        id: 'error-title',
        type: 'error',
        message: 'Спробуйте ще раз: введіть назву полотна ❌'
      });
      return;
    }
    setToast({
      id: 'success-title',
      type: 'success',
      message: 'Назву збережено! Оберіть template для генерації 🚀'
    });
    markStepDone(2, true);
  };

  // Action 3: Template Selection
  const handleTemplateSelect = (val: string) => {
    setSelectedTemplate(val);
    setToast({
      id: 'template-toast',
      type: 'success',
      message: `Шаблон "${val}" вибрано! Тепер натисніть 'Generate'`
    });
    markStepDone(3, true);
  };

  // Action 4: Generate Canvas Graph
  const handleGenerateClick = () => {
    setIsGenerating(true);
    setToast({
      id: 'generating-toast',
      type: 'pointer',
      message: 'AI Агент gerych_builder будує граф полотна...'
    });

    setTimeout(() => {
      setIsGenerating(false);
      setIsGenerated(true);
      setToast({
        id: 'generate-success',
        type: 'success',
        message: 'Полотно успішно згенеровано! Подивіться результат у превʼю'
      });
      markStepDone(4, true);
    }, 900);
  };

  // Action 5: View Result
  const handlePreviewAreaClick = () => {
    setPreviewClicked(true);
    setToast({
      id: 'preview-success',
      type: 'success',
      message: 'Вітаємо! Попередній перегляд активовано, граф готовий до роботи 🌟'
    });
    markStepDone(5, false);
    finalizeTutorial();
  };

  // Skip step handler
  const handleSkipStep = (stepId: number) => {
    markStepDone(stepId, true);
  };

  // Reset Tutorial
  const handleResetTutorial = () => {
    setCurrentStepIndex(0);
    setCompletedSteps([]);
    setIsGenerated(false);
    setPreviewClicked(false);
    setShowConfetti(false);
    try {
      localStorage.removeItem(STORAGE_TUTORIAL_COMPLETED);
      localStorage.removeItem(STORAGE_TUTORIAL_PROGRESS);
      localStorage.setItem(STORAGE_TUTORIAL_CURRENT_STEP, '0');
    } catch {}
    setToast({
      id: 'reset-toast',
      type: 'info',
      message: 'Туторіал скинуто до початку.'
    });
    logAnalytics('tutorial_started', { reset: true });
  };

  // Glow highlight class utility
  const getHighlightClass = (targetStepIndex: number) => {
    if (currentStepIndex === targetStepIndex) {
      return 'ring-4 ring-cyan-400 ring-offset-2 ring-offset-[#0b0f19] shadow-lg shadow-cyan-500/50 animate-pulse';
    }
    return '';
  };

  return (
    <div
      role="region"
      aria-label="Interactive Canvas Onboarding Tutorial"
      className={`w-full max-w-4xl mx-auto flex flex-col gap-5 ${
        isHighContrast ? 'bg-black text-white' : 'text-gray-100'
      } ${className}`}
    >
      {/* Top Controls: Accessibility & Sound & Reset */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-1">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <Layers className="w-5 h-5" aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span>Interactive Canvas Demo</span>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                Live Guided Tour
              </span>
            </h2>
            <p className="text-xs text-gray-400">
              Інтерактивне полотно: пройдіть 5 кроків для знайомства з функціоналом.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* High Contrast Toggle */}
          <button
            type="button"
            onClick={() => setIsHighContrast(!isHighContrast)}
            aria-pressed={isHighContrast}
            aria-label="Перемкнути режим високої контрастності"
            className="px-2.5 py-1 text-xs rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-gray-300 transition-colors"
          >
            {isHighContrast ? 'Стандартний' : 'Контрастність'}
          </button>

          {/* Reduced Motion Toggle */}
          <button
            type="button"
            onClick={() => setReducedMotion(!reducedMotion)}
            aria-pressed={reducedMotion}
            aria-label="Зменшена анімація"
            className="px-2.5 py-1 text-xs rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-gray-300 transition-colors"
          >
            {reducedMotion ? 'Анімація: Вимк' : 'Анімація: Увімк'}
          </button>

          {/* Reset Demo */}
          <button
            type="button"
            onClick={handleResetTutorial}
            aria-label="Скинути демо туторіал"
            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-gray-400 hover:text-white transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Real-time Feedback & Progress */}
      <RealTimeFeedback
        currentStep={currentStepIndex + 1}
        totalSteps={TUTORIAL_STEPS.length}
        toast={toast}
        onClearToast={() => setToast(null)}
        showConfetti={showConfetti}
        soundEnabled={soundEnabled}
        onToggleSound={setSoundEnabled}
        reducedMotion={reducedMotion}
      />

      {/* Step by Step Guide Overlay Card */}
      <StepByStepGuide
        currentStepIndex={currentStepIndex}
        onStepComplete={(id) => markStepDone(id, true)}
        onSkipStep={handleSkipStep}
        onSelectStep={(idx) => setCurrentStepIndex(idx)}
        isHighContrast={isHighContrast}
      />

      {/* Embedded Simulated Interactive Canvas Studio */}
      <div
        className={`rounded-2xl border ${
          isHighContrast ? 'border-cyan-400 bg-gray-950' : 'border-white/15 bg-[#0b0f19]'
        } p-4 sm:p-5 shadow-2xl relative overflow-hidden`}
      >
        {/* Studio Canvas Chrome Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-4 mb-5">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-rose-500/80" />
              <span className="w-3 h-3 rounded-full bg-amber-500/80" />
              <span className="w-3 h-3 rounded-full bg-emerald-500/80" />
            </div>
            <span className="text-xs font-mono text-gray-400">dnk-canvas://live-session</span>
          </div>

          {/* Interactive Toolbar Actions with Step Highlighting */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Step 1 Element: New Canvas Button */}
            <button
              id="tutorial-new-canvas-btn"
              type="button"
              onClick={handleNewCanvasClick}
              aria-label="Створити нове полотно (New Canvas)"
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black text-xs font-bold transition-all ${getHighlightClass(
                0
              )}`}
            >
              <Plus className="w-4 h-4" />
              <span>+ New Canvas</span>
            </button>

            {/* Step 2 Element: Canvas Title Input */}
            <div className="relative">
              <input
                id="tutorial-canvas-title-input"
                type="text"
                value={canvasTitle}
                onChange={(e) => handleTitleChange(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleTitleSubmit()}
                placeholder="Введіть назву полотна..."
                aria-label="Введіть назву полотна"
                className={`px-3 py-1.5 rounded-xl bg-white/5 border border-white/20 text-white text-xs placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-400 transition-all ${getHighlightClass(
                  1
                )}`}
              />
              {currentStepIndex === 1 && (
                <button
                  type="button"
                  onClick={handleTitleSubmit}
                  className="absolute right-1 top-1 bottom-1 px-2 rounded-lg bg-cyan-500 text-black text-[10px] font-bold"
                >
                  Зберегти
                </button>
              )}
            </div>

            {/* Step 3 Element: Template Select Dropdown */}
            <select
              id="tutorial-template-select"
              value={selectedTemplate}
              onChange={(e) => handleTemplateSelect(e.target.value)}
              aria-label="Оберіть template полотна"
              className={`px-3 py-1.5 rounded-xl bg-[#121826] border border-white/20 text-gray-200 text-xs focus:outline-none focus:ring-2 focus:ring-cyan-400 transition-all ${getHighlightClass(
                2
              )}`}
            >
              <option value="e-commerce">Template: E-commerce Launch</option>
              <option value="saas-landing">Template: SaaS Landing</option>
              <option value="ai-agent-swarm">Template: AI Agent Swarm</option>
            </select>

            {/* Step 4 Element: Generate Button */}
            <button
              id="tutorial-generate-btn"
              type="button"
              onClick={handleGenerateClick}
              disabled={isGenerating}
              aria-label="Натисніть Generate для створення структури"
              className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white text-xs font-semibold shadow-md transition-all ${getHighlightClass(
                3
              )} ${isGenerating ? 'opacity-70 cursor-wait' : ''}`}
            >
              {isGenerating ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Генерація...</span>
                </>
              ) : (
                <>
                  <Wand2 className="w-3.5 h-3.5" />
                  <span>Generate</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Step 5 Element: Canvas Preview Area */}
        <div
          id="tutorial-canvas-preview"
          role="button"
          tabIndex={0}
          onClick={handlePreviewAreaClick}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              handlePreviewAreaClick();
            }
          }}
          aria-label="Область попереднього перегляду полотна Canvas. Клацніть для активації"
          className={`w-full min-h-[220px] rounded-xl border border-dashed border-white/20 bg-[#060911]/80 p-4 transition-all flex flex-col justify-between cursor-pointer ${getHighlightClass(
            4
          )} ${previewClicked ? 'border-emerald-500/60 bg-emerald-950/10' : ''}`}
        >
          {/* Canvas Sub-header */}
          <div className="flex items-center justify-between text-xs text-gray-400 mb-3">
            <span className="flex items-center gap-1.5 font-mono">
              <Layout className="w-3.5 h-3.5 text-cyan-400" />
              <span>Project: {canvasTitle || 'Untitled'} ({selectedTemplate})</span>
            </span>
            <span className="text-[11px] text-cyan-400 font-semibold">
              {isGenerated ? 'Status: 100% Generated' : 'Status: Ready for Generation'}
            </span>
          </div>

          {/* Simulated Graph Nodes */}
          {isGenerated ? (
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 my-auto py-2">
              {INITIAL_MOCK_NODES.map((node) => (
                <div
                  key={node.id}
                  className="p-3 rounded-xl bg-white/[0.04] border border-cyan-500/30 flex flex-col gap-1.5 shadow-md"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] uppercase font-mono text-cyan-400">
                      {node.type}
                    </span>
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                  </div>
                  <span className="text-xs font-bold text-white">{node.title}</span>
                  <span className="text-[10px] text-gray-400">Node status: Ready</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="my-auto text-center py-6">
              <Sparkles className="w-8 h-8 text-cyan-500/60 mx-auto mb-2 animate-bounce" />
              <p className="text-xs text-gray-300 font-medium">
                Натисніть кнопку 'Generate' вище, щоб заповнити полотно автономними вузлами рою.
              </p>
              <p className="text-[11px] text-gray-500 mt-1">
                Клік по цій області після генерації завершить крок 5!
              </p>
            </div>
          )}

          {/* Canvas Footer */}
          <div className="flex items-center justify-between text-[11px] text-gray-500 border-t border-white/5 pt-2 mt-3">
            <span>Graph Engine: CanvasEngine v4.5</span>
            <span className="text-cyan-400">Клікніть для перегляду</span>
          </div>
        </div>
      </div>

      {/* Achievement Badges Section */}
      <div className="rounded-2xl border border-white/10 bg-[#0b0f19] p-4 sm:p-5">
        <AchievementBadges badges={badges} />
      </div>

      {/* Exit or Next Step CTA */}
      {onExit && (
        <div className="flex justify-end pt-2">
          <button
            type="button"
            onClick={onExit}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 text-xs font-semibold transition-colors"
          >
            <span>Повернутися до онбордингу</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};

export default InteractiveCanvasDemo;
