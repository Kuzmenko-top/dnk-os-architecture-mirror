// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_StitchPromptDock"
// purpose: "Google Stitch Floating Command Bar matching exact specs"
// author: "DNK-e.com Maksym"
// status: "Active"
// version: "3.0.0"
// updated_at: "2026-09-03"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Plus, Sliders, Image, Mic, ArrowUp } from 'lucide-react';

interface StitchPromptDockProps {
  onSubmitPrompt: (prompt: string) => void;
  isLoading?: boolean;
}

export default function StitchPromptDock({ onSubmitPrompt, isLoading = false }: StitchPromptDockProps) {
  const [prompt, setPrompt] = useState('');
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  const toggleVoiceInput = () => {
    if (isListening) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsListening(false);
      return;
    }

    const SpeechRec = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRec) {
      // Fallback prompt for environments without native Web Speech API
      const fallbackVoice = 'Герич, покажи аналітику доходів';
      setPrompt(fallbackVoice);
      return;
    }

    try {
      const recognition = new SpeechRec();
      recognition.lang = 'uk-UA';
      recognition.continuous = false;
      recognition.interimResults = true;

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event: any) => {
        const transcript = Array.from(event.results)
          .map((result: any) => result[0].transcript)
          .join('');
        setPrompt(transcript);
      };

      recognition.onerror = () => {
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch {
      setIsListening(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim() && !isLoading) {
      onSubmitPrompt(prompt);
      setPrompt('');
    }
  };

  return (
    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-30 w-full max-w-2xl px-4">
      <form
        onSubmit={handleSubmit}
        className="flex items-center gap-3 bg-[#16181f]/90 border border-white/10 rounded-full py-2.5 px-4 shadow-2xl backdrop-blur-2xl focus-within:border-[#33EE75]/50 transition-colors"
      >
        {/* Left Control Group */}
        <div className="flex items-center gap-2 text-neutral-400">
          <button
            type="button"
            className="p-1.5 hover:text-white hover:bg-white/5 rounded-full transition-colors"
            title="Add to prompt"
          >
            <Plus className="w-4 h-4" />
          </button>
          <button
            type="button"
            className="p-1.5 hover:text-white hover:bg-white/5 rounded-full transition-colors"
            title="System prompt shortcuts"
          >
            <span className="text-xs font-mono font-bold">/</span>
          </button>
          <button
            type="button"
            className="p-1.5 hover:text-white hover:bg-white/5 rounded-full transition-colors"
            title="Upload design screenshot"
          >
            <Image className="w-4 h-4" />
          </button>
        </div>

        {/* Divider */}
        <div className="h-5 w-px bg-white/10" />

        {/* Dynamic Text Input */}
        <input
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="What would you like to change or create?"
          className="flex-1 bg-transparent border-none outline-none text-sm text-neutral-200 placeholder-neutral-500 font-sans py-1"
        />

        {/* Right Settings & Submit Group */}
        <div className="flex items-center gap-2">
          {/* Model Mode Selection Pill */}
          <button
            type="button"
            className="flex items-center gap-1.5 bg-[#20222a] border border-white/5 rounded-full px-2.5 py-1 text-[10px] font-semibold text-neutral-300 hover:text-white hover:bg-white/5 transition-colors"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-coral-400 bg-orange-400 animate-pulse" />
            <span>Balanced</span>
          </button>

          <button
            type="button"
            onClick={toggleVoiceInput}
            className={`p-1.5 rounded-full transition-all ${
              isListening
                ? 'bg-red-500/20 text-red-400 border border-red-500/40 animate-pulse'
                : 'text-neutral-400 hover:text-white hover:bg-white/5'
            }`}
            title={isListening ? 'Зупинити запис голосу' : 'Голосове введення (uk-UA)'}
          >
            <Mic className="w-4 h-4" />
          </button>

          <button
            type="submit"
            disabled={!prompt.trim() || isLoading}
            className={`p-2 rounded-full transition-all ${
              prompt.trim() && !isLoading
                ? 'bg-white text-black hover:scale-105 active:scale-95'
                : 'bg-white/10 text-neutral-500 cursor-not-allowed'
            }`}
          >
            <ArrowUp className="w-4 h-4 stroke-[3]" />
          </button>
        </div>
      </form>
    </div>
  );
}
