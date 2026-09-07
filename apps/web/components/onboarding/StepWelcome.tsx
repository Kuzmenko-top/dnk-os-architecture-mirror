// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/onboarding/StepWelcome.tsx"
// purpose: "Welcome Step 1 for DNK OS Interactive Onboarding Wizard"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-05"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---

'use client';

import React from 'react';
import { Sparkles, ArrowRight, ShieldCheck, Cpu, Zap } from 'lucide-react';

export interface StepWelcomeProps {
  onNext: () => void;
  onSkip: () => void;
}

export const StepWelcome: React.FC<StepWelcomeProps> = ({ onNext, onSkip }) => {
  return (
    <section
      aria-label="Вітальний крок онбордингу"
      className="flex flex-col items-center text-center py-6 px-4 max-w-2xl mx-auto"
    >
      {/* Visual Logo / Illustration */}
      <div className="relative mb-6">
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-cyan-500 via-indigo-500 to-purple-600 p-[2px] shadow-lg shadow-indigo-500/20">
          <div className="w-full h-full bg-[#0b0f19] rounded-2xl flex items-center justify-center">
            <Sparkles className="w-10 h-10 text-cyan-400 animate-pulse" aria-hidden="true" />
          </div>
        </div>
        <span className="absolute -top-1 -right-1 flex h-4 w-4">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-4 w-4 bg-cyan-500"></span>
        </span>
      </div>

      {/* Main Welcome Headline */}
      <h2 className="text-3xl font-extrabold tracking-tight text-white mb-3">
        Ласкаво просимо до <span className="bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500 bg-clip-text text-transparent">DNK OS</span>
      </h2>

      {/* 2-3 Sentences Description */}
      <p className="text-gray-300 text-base leading-relaxed mb-6">
        DNK OS — це автономна операційна система на базі мультиагентного рою з 14 спеціалізованих агентів.
        Вона поєднує інтерактивне безмежне полотно Canvas, довготривалу памʼять SCONES та миттєвий запуск цифрових продуктів.
        Пройдіть швидкий інтерактивний тур, щоб опанувати всі можливості за лічені хвилини.
      </p>

      {/* Highlights / Badges */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full mb-8">
        <div className="p-3.5 rounded-xl bg-white/[0.03] border border-white/10 flex flex-col items-center">
          <Cpu className="w-5 h-5 text-cyan-400 mb-1.5" aria-hidden="true" />
          <span className="text-xs font-semibold text-gray-200">14 AI Агентів</span>
          <span className="text-[11px] text-gray-400">Повна автономія</span>
        </div>
        <div className="p-3.5 rounded-xl bg-white/[0.03] border border-white/10 flex flex-col items-center">
          <Zap className="w-5 h-5 text-amber-400 mb-1.5" aria-hidden="true" />
          <span className="text-xs font-semibold text-gray-200">Zero-Waste Стек</span>
          <span className="text-[11px] text-gray-400">10x швидкість розробки</span>
        </div>
        <div className="p-3.5 rounded-xl bg-white/[0.03] border border-white/10 flex flex-col items-center">
          <ShieldCheck className="w-5 h-5 text-emerald-400 mb-1.5" aria-hidden="true" />
          <span className="text-xs font-semibold text-gray-200">SCONES Vault</span>
          <span className="text-[11px] text-gray-400">Безпечна памʼять</span>
        </div>
      </div>

      {/* CTA Buttons */}
      <div className="flex flex-col sm:flex-row items-center gap-3 w-full justify-center">
        <button
          onClick={onNext}
          type="button"
          aria-label="Розпочати тур по системі"
          className="w-full sm:w-auto px-7 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-medium text-sm flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/25 transition-all transform active:scale-95"
        >
          <span>Розпочати тур</span>
          <ArrowRight className="w-4 h-4" aria-hidden="true" />
        </button>
        <button
          onClick={onSkip}
          type="button"
          aria-label="Пропустити онбординг"
          className="w-full sm:w-auto px-6 py-3 rounded-xl bg-transparent hover:bg-white/[0.05] text-gray-400 hover:text-gray-200 font-medium text-sm transition-colors border border-transparent hover:border-white/10"
        >
          Пропустити
        </button>
      </div>
    </section>
  );
};

export default StepWelcome;
