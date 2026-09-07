// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/tutorial/RealTimeFeedback.tsx"
// purpose: "Real-time Feedback Toasts, Web Audio Synthesized Chimes/Buzzers, and Confetti Animation"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-05"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useEffect, useState, useCallback, useRef } from 'react';
import {
  CheckCircle2,
  XCircle,
  ArrowRight,
  Volume2,
  VolumeX,
  Sparkles,
  Info
} from 'lucide-react';

export type FeedbackType = 'success' | 'error' | 'pointer' | 'info';

export const DEFAULT_FEEDBACK_MESSAGES = {
  success: "Чудово! Ви створили полотно",
  error: "Спробуйте ще раз",
  pointer: "Натисніть сюди"
};

export const CONFETTI_PARTICLES_COUNT = 24;

export interface ToastMessage {
  id: string;
  type: FeedbackType;
  message: string;
  durationMs?: number;
}

export interface RealTimeFeedbackProps {
  currentStep: number;
  totalSteps: number;
  toast: ToastMessage | null;
  onClearToast?: () => void;
  showConfetti?: boolean;
  soundEnabled?: boolean;
  onToggleSound?: (enabled: boolean) => void;
  className?: string;
  reducedMotion?: boolean;
}

// Client-side Web Audio API Sound Synthesizer (zero external asset dependency)
class SoundSynthesizer {
  private ctx: AudioContext | null = null;

  private initContext() {
    if (typeof window === 'undefined') return null;
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {});
    }
    return this.ctx;
  }

  playSuccessChime() {
    try {
      const ctx = this.initContext();
      if (!ctx) return;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sine';
      // Harmonic chime arpeggio: 587.33Hz (D5) -> 880Hz (A5)
      osc.frequency.setValueAtTime(587.33, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.15);

      gain.gain.setValueAtTime(0.12, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start();
      osc.stop(ctx.currentTime + 0.4);
    } catch {
      // Audio not permitted or failed gracefully
    }
  }

  playErrorBuzz() {
    try {
      const ctx = this.initContext();
      if (!ctx) return;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sawtooth';
      // Low buzz: 160Hz -> 120Hz
      osc.frequency.setValueAtTime(160, ctx.currentTime);
      osc.frequency.setValueAtTime(120, ctx.currentTime + 0.1);

      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start();
      osc.stop(ctx.currentTime + 0.3);
    } catch {
      // Audio not permitted or failed gracefully
    }
  }
}

const synthesizer = new SoundSynthesizer();

export const RealTimeFeedback: React.FC<RealTimeFeedbackProps> = ({
  currentStep,
  totalSteps,
  toast,
  onClearToast,
  showConfetti = false,
  soundEnabled = false,
  onToggleSound,
  className = '',
  reducedMotion = false
}) => {
  const [internalSoundEnabled, setInternalSoundEnabled] = useState<boolean>(soundEnabled);
  const isSoundOn = onToggleSound !== undefined ? soundEnabled : internalSoundEnabled;

  const toggleSound = () => {
    const nextVal = !isSoundOn;
    if (onToggleSound) {
      onToggleSound(nextVal);
    } else {
      setInternalSoundEnabled(nextVal);
    }
  };

  // Play sound when toast changes
  useEffect(() => {
    if (!toast || !isSoundOn) return;
    if (toast.type === 'success') {
      synthesizer.playSuccessChime();
    } else if (toast.type === 'error') {
      synthesizer.playErrorBuzz();
    }
  }, [toast, isSoundOn]);

  // Auto-dismiss toast
  useEffect(() => {
    if (!toast) return;
    const duration = toast.durationMs || 3500;
    const timer = setTimeout(() => {
      if (onClearToast) onClearToast();
    }, duration);
    return () => clearTimeout(timer);
  }, [toast, onClearToast]);

  const progressPercentage = Math.min(100, Math.max(0, (currentStep / totalSteps) * 100));

  return (
    <div className={`relative w-full ${className}`}>
      {/* Top Bar: Progress and Sound Toggle */}
      <div className="flex items-center justify-between gap-3 mb-2 px-1">
        <div className="flex items-center gap-2">
          <span
            id="tutorial-progress-label"
            className="text-xs font-semibold text-gray-300 font-mono"
          >
            Крок {currentStep} з {totalSteps}
          </span>
          <span className="text-[11px] text-gray-500">
            ({Math.round(progressPercentage)}%)
          </span>
        </div>

        <button
          type="button"
          onClick={toggleSound}
          aria-label={isSoundOn ? 'Вимкнути звукові ефекти' : 'Увімкнути звукові ефекти'}
          aria-pressed={isSoundOn}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white/5 hover:bg-white/10 text-gray-400 hover:text-gray-200 text-xs transition-colors border border-white/10 focus:outline-none focus:ring-2 focus:ring-cyan-400"
        >
          {isSoundOn ? (
            <>
              <Volume2 className="w-3.5 h-3.5 text-cyan-400" aria-hidden="true" />
              <span className="text-[11px]">Звук увімкнено</span>
            </>
          ) : (
            <>
              <VolumeX className="w-3.5 h-3.5 text-gray-500" aria-hidden="true" />
              <span className="text-[11px]">Звук вимкнено (Muted)</span>
            </>
          )}
        </button>
      </div>

      {/* Progress Bar */}
      <div
        role="progressbar"
        aria-labelledby="tutorial-progress-label"
        aria-valuenow={currentStep}
        aria-valuemin={1}
        aria-valuemax={totalSteps}
        className="w-full bg-gray-800/80 h-2 rounded-full overflow-hidden mb-4 border border-white/5"
      >
        <div
          className={`h-full bg-gradient-to-r from-cyan-400 via-blue-500 to-emerald-400 ${
            reducedMotion ? '' : 'transition-all duration-300'
          }`}
          style={{ width: `${progressPercentage}%` }}
        />
      </div>

      {/* Real-time Toast Banner with ARIA live region */}
      <div
        aria-live="polite"
        aria-atomic="true"
        className="min-h-[44px] flex items-center justify-center"
      >
        {toast && (
          <div
            role={toast.type === 'error' ? 'alert' : 'status'}
            className={`w-full p-3 rounded-xl border flex items-center justify-between gap-3 text-xs font-medium shadow-lg transition-all ${
              reducedMotion ? '' : 'animate-fadeIn'
            } ${
              toast.type === 'success'
                ? 'bg-emerald-950/60 border-emerald-500/50 text-emerald-200'
                : toast.type === 'error'
                ? 'bg-rose-950/60 border-rose-500/50 text-rose-200'
                : toast.type === 'pointer'
                ? 'bg-cyan-950/60 border-cyan-500/50 text-cyan-200'
                : 'bg-gray-900/80 border-gray-700 text-gray-200'
            }`}
          >
            <div className="flex items-center gap-2.5">
              {toast.type === 'success' && (
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" aria-hidden="true" />
              )}
              {toast.type === 'error' && (
                <XCircle className="w-4 h-4 text-rose-400 shrink-0" aria-hidden="true" />
              )}
              {toast.type === 'pointer' && (
                <ArrowRight className="w-4 h-4 text-cyan-400 shrink-0 animate-pulse" aria-hidden="true" />
              )}
              {toast.type === 'info' && (
                <Info className="w-4 h-4 text-blue-400 shrink-0" aria-hidden="true" />
              )}
              <span className="leading-snug">{toast.message}</span>
            </div>

            {onClearToast && (
              <button
                type="button"
                onClick={onClearToast}
                aria-label="Закрити сповіщення"
                className="text-gray-400 hover:text-white p-1 rounded-md hover:bg-white/10 transition-colors"
              >
                ✕
              </button>
            )}
          </div>
        )}
      </div>

      {/* Pure CSS/SVG Confetti Animation Particles */}
      {showConfetti && (
        <div
          role="presentation"
          aria-hidden="true"
          className="pointer-events-none absolute -top-8 left-0 right-0 h-40 overflow-hidden flex justify-center items-start z-50"
        >
          {Array.from({ length: 24 }).map((_, i) => {
            const colors = ['#22d3ee', '#10b981', '#3b82f6', '#f59e0b', '#ec4899', '#a855f7'];
            const color = colors[i % colors.length];
            const left = `${(i / 24) * 100}%`;
            const delay = `${(i % 5) * 0.15}s`;
            const duration = `${1.2 + (i % 3) * 0.3}s`;
            return (
              <span
                key={i}
                className="absolute w-2.5 h-2.5 rounded-sm transform origin-center animate-confetti-fall"
                style={{
                  backgroundColor: color,
                  left,
                  animationDelay: delay,
                  animationDuration: duration,
                  opacity: 0.9
                }}
              />
            );
          })}
        </div>
      )}
    </div>
  );
};

export default RealTimeFeedback;
