// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/onboarding/OnboardingWizard.tsx"
// purpose: "Unified 5-Step Interactive Onboarding Wizard with LocalStorage persistence & WCAG 2.1 AA accessibility"
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
  X,
  CheckCircle2,
  BookOpen,
  Search,
  ExternalLink,
  ArrowRight,
  ArrowLeft,
  PartyPopper,
  Users,
  LifeBuoy,
  PlusCircle
} from 'lucide-react';
import StepWelcome from './StepWelcome';
import StepTutorial from './StepTutorial';
import StepVideoGuides from './StepVideoGuides';

export interface OnboardingWizardProps {
  isOpen?: boolean;
  onClose?: () => void;
  standalone?: boolean;
  onComplete?: () => void;
}

const TOTAL_STEPS = 5;
const STORAGE_COMPLETED_KEY = 'dnk_onboarding_completed';
const STORAGE_STEPS_KEY = 'dnk_onboarding_completed_steps';

export const OnboardingWizard: React.FC<OnboardingWizardProps> = ({
  isOpen = true,
  onClose,
  standalone = false,
  onComplete,
}) => {
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  // Hydrate from localStorage on client mount
  useEffect(() => {
    try {
      const savedSteps = localStorage.getItem(STORAGE_STEPS_KEY);
      if (savedSteps) {
        const parsed = JSON.parse(savedSteps);
        if (Array.isArray(parsed)) {
          setCompletedSteps(parsed);
        }
      }
    } catch {
      // Ignore localStorage errors (e.g., SSR or private browsing)
    }
  }, []);

  const persistStepCompletion = (step: number) => {
    try {
      const updated = Array.from(new Set([...completedSteps, step]));
      setCompletedSteps(updated);
      localStorage.setItem(STORAGE_STEPS_KEY, JSON.stringify(updated));
    } catch {
      // Ignore storage errors
    }
  };

  const handleNext = () => {
    persistStepCompletion(currentStep);
    if (currentStep < TOTAL_STEPS) {
      setCurrentStep(prev => prev + 1);
    } else {
      finishOnboarding();
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleSkip = () => {
    finishOnboarding();
  };

  const finishOnboarding = () => {
    try {
      localStorage.setItem(STORAGE_COMPLETED_KEY, 'true');
      const allSteps = [1, 2, 3, 4, 5];
      setCompletedSteps(allSteps);
      localStorage.setItem(STORAGE_STEPS_KEY, JSON.stringify(allSteps));
    } catch {
      // Ignore storage errors
    }
    if (onComplete) onComplete();
    if (onClose) onClose();
  };

  if (!isOpen && !standalone) {
    return null;
  }

  const progressPercentage = (currentStep / TOTAL_STEPS) * 100;

  // Step 4: Knowledge Base
  const renderKnowledgeBase = () => {
    const kbLinks = [
      {
        title: 'Getting Started Guide',
        desc: 'Повний 5-хвилинний посібник з перших кроків у DNK OS',
        url: '/docs/user-guides/GETTING_STARTED.md',
      },
      {
        title: 'API Reference',
        desc: 'Специфікація REST та WebSocket ендпоінтів бекенду',
        url: '/docs/api/README.md',
      },
      {
        title: 'Best Practices',
        desc: 'Шаблони розгортання рою агентів та Zero-Waste протокол',
        url: '/docs/templates/GERYCH_TASK_TEMPLATE.md',
      },
      {
        title: 'FAQ & Troubleshooting',
        desc: 'Відповіді на часті питання та рішення типових проблем',
        url: '/docs/user-guides/GETTING_STARTED.md#5-поширені-запитання-faq',
      },
    ];

    const filtered = kbLinks.filter(item =>
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.desc.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
      <section aria-label="База знань та документація" className="flex flex-col py-4 px-3 max-w-2xl mx-auto w-full">
        <div className="text-center mb-5">
          <h2 className="text-2xl font-bold text-white mb-2 flex items-center justify-center gap-2">
            <BookOpen className="w-6 h-6 text-cyan-400" aria-hidden="true" />
            База знань та документація
          </h2>
          <p className="text-sm text-gray-300">
            Отримайте миттєвий доступ до офіційної документації, прикладів коду та кращих практик.
          </p>
        </div>

        {/* Search Bar */}
        <div className="relative mb-5">
          <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" aria-hidden="true" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Що ви хочете дізнатися?"
            aria-label="Що ви хочете дізнатися?"
            className="w-full bg-[#0b0f19] border border-white/15 focus:border-cyan-500 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-gray-500 outline-none transition-colors"
          />
        </div>

        {/* Documentation Links */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-5">
          {filtered.map((link, idx) => (
            <a
              key={idx}
              href={link.url}
              target="_blank"
              rel="noopener noreferrer"
              className="p-3.5 rounded-xl bg-white/[0.03] hover:bg-white/[0.07] border border-white/10 hover:border-cyan-500/40 transition-all group flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <h3 className="text-sm font-semibold text-white group-hover:text-cyan-300 transition-colors">
                    {link.title}
                  </h3>
                  <ExternalLink className="w-3.5 h-3.5 text-gray-400 group-hover:text-cyan-400 transition-colors" />
                </div>
                <p className="text-xs text-gray-400 leading-relaxed">{link.desc}</p>
              </div>
            </a>
          ))}
        </div>

        {/* CTA: Відкрити документацію */}
        <div className="flex justify-center mb-6">
          <a
            href="/docs/user-guides/GETTING_STARTED.md"
            target="_blank"
            rel="noopener noreferrer"
            className="px-5 py-2.5 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] text-cyan-300 hover:text-white border border-cyan-500/30 text-xs font-semibold flex items-center gap-2 transition-colors"
          >
            <span>Відкрити документацію</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>

        {/* Navigation Footer */}
        <div className="flex items-center justify-between w-full pt-2">
          <button
            onClick={handleBack}
            type="button"
            className="px-4 py-2.5 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] text-gray-300 text-xs font-medium flex items-center gap-1.5 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Назад</span>
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={handleSkip}
              type="button"
              className="px-3 py-2 text-gray-400 hover:text-gray-200 text-xs transition-colors"
            >
              Пропустити
            </button>
            <button
              onClick={handleNext}
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

  // Step 5: Completion
  const renderCompletion = () => {
    return (
      <section aria-label="Завершення онбордингу" className="flex flex-col items-center text-center py-6 px-4 max-w-2xl mx-auto">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-emerald-500 to-cyan-500 p-[2px] mb-4 shadow-lg shadow-emerald-500/20">
          <div className="w-full h-full bg-[#0b0f19] rounded-2xl flex items-center justify-center">
            <PartyPopper className="w-8 h-8 text-emerald-400 animate-bounce" aria-hidden="true" />
          </div>
        </div>

        <h2 className="text-3xl font-extrabold text-white mb-2">
          Вітаємо! Ви готові до роботи
        </h2>
        <p className="text-gray-300 text-sm max-w-lg mb-6 leading-relaxed">
          Ви успішно пройшли всі етапи знайомства з DNK OS. Тепер вам доступна вся міць автономного рою агентів, візуального полотна та швидкого запуску проектів.
        </p>

        {/* Social Proof */}
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-medium mb-8">
          <Users className="w-4 h-4" />
          <span>1000+ користувачів вже використовують DNK OS</span>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full mb-8">
          <button
            onClick={finishOnboarding}
            type="button"
            className="p-4 rounded-xl bg-cyan-600/20 hover:bg-cyan-600/30 border border-cyan-500/40 text-left transition-all group flex flex-col justify-between"
          >
            <PlusCircle className="w-5 h-5 text-cyan-400 mb-2 group-hover:scale-110 transition-transform" />
            <div>
              <span className="text-xs font-bold text-white block">Створити полотно</span>
              <span className="text-[11px] text-gray-400">Розпочати новий проект</span>
            </div>
          </button>

          <a
            href="/docs/user-guides/GETTING_STARTED.md"
            target="_blank"
            rel="noopener noreferrer"
            className="p-4 rounded-xl bg-white/[0.03] hover:bg-white/[0.06] border border-white/10 text-left transition-all group flex flex-col justify-between"
          >
            <BookOpen className="w-5 h-5 text-indigo-400 mb-2 group-hover:scale-110 transition-transform" />
            <div>
              <span className="text-xs font-bold text-white block">Відкрити документацію</span>
              <span className="text-[11px] text-gray-400">Переглянути посібники</span>
            </div>
          </a>

          <a
            href="https://t.me/dnk_os_support"
            target="_blank"
            rel="noopener noreferrer"
            className="p-4 rounded-xl bg-white/[0.03] hover:bg-white/[0.06] border border-white/10 text-left transition-all group flex flex-col justify-between"
          >
            <LifeBuoy className="w-5 h-5 text-amber-400 mb-2 group-hover:scale-110 transition-transform" />
            <div>
              <span className="text-xs font-bold text-white block">Зв'язатися з підтримкою</span>
              <span className="text-[11px] text-gray-400">Отримати допомогу</span>
            </div>
          </a>
        </div>

        {/* Final Completion CTA */}
        <button
          onClick={finishOnboarding}
          type="button"
          className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-white font-bold text-sm flex items-center justify-center gap-2 shadow-xl shadow-emerald-500/20 transition-all transform active:scale-95"
        >
          <CheckCircle2 className="w-5 h-5" />
          <span>Перейти до робочого простору</span>
        </button>
      </section>
    );
  };

  const wizardContent = (
    <div className="w-full max-w-3xl bg-[#07090e] border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col text-white">
      {/* Header with Title and Progress */}
      <header className="px-6 py-4 border-b border-white/10 bg-[#0b0f19]/80 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-cyan-400 bg-cyan-500/10 px-2.5 py-1 rounded-md border border-cyan-500/20">
              DNK OS Onboarding
            </span>
            <span className="text-xs text-gray-400">
              Крок {currentStep} з {TOTAL_STEPS} (Step {currentStep} of {TOTAL_STEPS})
            </span>
          </div>

          {onClose && (
            <button
              onClick={onClose}
              aria-label="Закрити вікно онбордингу"
              className="text-gray-400 hover:text-white p-1 rounded-lg hover:bg-white/10 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Progress Bar (Step 1 of 5) */}
        <div className="w-full bg-gray-800 h-1.5 rounded-full overflow-hidden" role="progressbar" aria-valuenow={currentStep} aria-valuemin={1} aria-valuemax={TOTAL_STEPS}>
          <div
            className="h-full bg-gradient-to-r from-cyan-400 via-indigo-500 to-emerald-400 transition-all duration-300"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
      </header>

      {/* Dynamic Step View */}
      <main className="p-4 sm:p-6 flex-1 min-h-[380px] flex items-center">
        {currentStep === 1 && (
          <StepWelcome onNext={handleNext} onSkip={handleSkip} />
        )}
        {currentStep === 2 && (
          <StepTutorial onNext={handleNext} onBack={handleBack} onSkip={handleSkip} />
        )}
        {currentStep === 3 && (
          <StepVideoGuides onNext={handleNext} onBack={handleBack} onSkip={handleSkip} />
        )}
        {currentStep === 4 && renderKnowledgeBase()}
        {currentStep === 5 && renderCompletion()}
      </main>
    </div>
  );

  if (standalone) {
    return (
      <div className="min-h-screen bg-[#04060a] flex items-center justify-center p-4">
        {wizardContent}
      </div>
    );
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="DNK OS Онбординг-візард"
      className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto"
    >
      {wizardContent}
    </div>
  );
};

export default OnboardingWizard;
