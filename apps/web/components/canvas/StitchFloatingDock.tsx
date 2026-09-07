// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_StitchFloatingDock"
// purpose: "Floating Stitch Prompt Dock with dark glassmorphism, model selector, neon active glows, and quick templates for spawning/linking Video, Shopify, and Photo nodes"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-03"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { 
  Sparkles, 
  Send, 
  Mic, 
  Film, 
  ShoppingBag, 
  Camera, 
  Cpu, 
  Globe, 
  ArrowRight,
  Settings,
  X
} from 'lucide-react';

interface StitchFloatingDockProps {
  onSubmit: (prompt: string, type: 'video' | 'shopify' | 'photo' | 'general') => void;
  onClose?: () => void;
}

export default function StitchFloatingDock({ onSubmit, onClose }: StitchFloatingDockProps) {
  const [prompt, setPrompt] = useState('');
  const [selectedType, setSelectedType] = useState<'video' | 'shopify' | 'photo' | 'general'>('general');
  const [activeModel, setActiveModel] = useState('gemini-2.5-flash');
  const [isListening, setIsListening] = useState(false);

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    if (!prompt.trim()) return;
    onSubmit(prompt, selectedType);
    setPrompt('');
  };

  const handleMicClick = () => {
    setIsListening(!isListening);
    if (!isListening) {
      // Simulate listening feedback
      setTimeout(() => {
        setPrompt("Створити нове 9:16 UGC відео-прев'ю для ReBurn коктейльного смокера");
        setIsListening(false);
      }, 1800);
    }
  };

  return (
    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-40 w-full max-w-3xl px-4 transition-all duration-300">
      <div className="relative rounded-2xl bg-[#02090a]/90 backdrop-blur-2xl border border-[#1e2c31] hover:border-[#36f4a4]/40 p-4 shadow-[0_20px_50px_rgba(0,0,0,0.85)] flex flex-col gap-3 transition-colors duration-200">
        
        {/* Decorative Neon Inner Border Accent */}
        <div className="absolute inset-0 rounded-2xl pointer-events-none border border-[#36f4a4]/5 shadow-[inset_0_0_20px_rgba(54,244,164,0.02)]" />

        {/* Quick Options Header & Model Selector */}
        <div className="flex items-center justify-between text-xs font-mono text-[#a1a1aa] relative z-10">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5 text-[#36f4a4] font-bold">
              <Sparkles className="w-3.5 h-3.5 animate-pulse" />
              <span>STITCH AI SWARM</span>
            </span>
            <span className="text-[#3a4e4d]">|</span>
            <div className="flex items-center gap-1.5 bg-[#061a1c] border border-[#1e2c31] rounded-full px-2.5 py-1">
              <Cpu className="w-3 h-3 text-[#22d3ee]" />
              <select 
                value={activeModel} 
                onChange={(e) => setActiveModel(e.target.value)}
                className="bg-transparent border-none text-[10px] text-[#22d3ee] font-bold font-mono focus:outline-none focus:ring-0 cursor-pointer"
              >
                <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
                <option value="gemini-2.5-pro">Gemini 2.5 Pro</option>
                <option value="gerych-core-v4">Gerych Core v4</option>
              </select>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[10px] text-[#71717a]">Press Enter to spawn & link</span>
            {onClose && (
              <button 
                onClick={onClose} 
                className="p-1 rounded-full hover:bg-[#061a1c] text-[#71717a] hover:text-white transition-colors"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        </div>

        {/* Type Selector Pills */}
        <div className="flex items-center gap-2 relative z-10">
          <button
            onClick={() => setSelectedType('general')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-mono transition-all cursor-pointer ${
              selectedType === 'general'
                ? 'bg-[#061a1c] border-[#36f4a4]/40 text-[#36f4a4] shadow-[0_0_12px_rgba(54,244,164,0.15)] font-bold'
                : 'bg-transparent border-[#1e2c31] text-[#71717a] hover:text-[#d4d4d8]'
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            <span>General Idea</span>
          </button>

          <button
            onClick={() => setSelectedType('video')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-mono transition-all cursor-pointer ${
              selectedType === 'video'
                ? 'bg-[#102620] border-[#36f4a4]/60 text-[#36f4a4] shadow-[0_0_12px_rgba(54,244,164,0.2)] font-bold'
                : 'bg-transparent border-[#1e2c31] text-[#71717a] hover:text-[#d4d4d8]'
            }`}
          >
            <Film className="w-3.5 h-3.5" />
            <span>Video Reel</span>
          </button>

          <button
            onClick={() => setSelectedType('shopify')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-mono transition-all cursor-pointer ${
              selectedType === 'shopify'
                ? 'bg-[#081e2b] border-[#22d3ee]/60 text-[#22d3ee] shadow-[0_0_12px_rgba(34,211,238,0.2)] font-bold'
                : 'bg-transparent border-[#1e2c31] text-[#71717a] hover:text-[#d4d4d8]'
            }`}
          >
            <ShoppingBag className="w-3.5 h-3.5" />
            <span>Shopify Section</span>
          </button>

          <button
            onClick={() => setSelectedType('photo')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-mono transition-all cursor-pointer ${
              selectedType === 'photo'
                ? 'bg-[#1e112c] border-[#c084fc]/60 text-[#c084fc] shadow-[0_0_12px_rgba(192,132,252,0.2)] font-bold'
                : 'bg-transparent border-[#1e2c31] text-[#71717a] hover:text-[#d4d4d8]'
            }`}
          >
            <Camera className="w-3.5 h-3.5" />
            <span>Brand Photo</span>
          </button>
        </div>

        {/* Input Bar */}
        <div className="flex items-center gap-2 bg-[#02090a] border border-[#1e2c31] rounded-xl p-1.5 pl-3 relative z-10 focus-within:border-[#36f4a4]/40 transition-colors duration-200">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder={
              selectedType === 'video' 
                ? "Describe the video script or UGC reel idea (e.g. 'Cyberpunk Cocktail Smoker reveal')..."
                : selectedType === 'shopify'
                ? "Describe custom liquid section requirements (e.g. 'Dynamic product bundle card with live countdown')..."
                : selectedType === 'photo'
                ? "Describe branding photography concepts or background scenery..."
                : "Type your strategic idea or task and let Stitch build..."
            }
            className="flex-1 bg-transparent border-none text-sm text-white focus:outline-none focus:ring-0 placeholder-[#4c5c5c] font-sans"
          />

          <button
            onClick={handleMicClick}
            className={`p-2 rounded-lg transition-colors cursor-pointer ${
              isListening 
                ? 'bg-red-500/20 text-red-400 animate-pulse' 
                : 'hover:bg-[#061a1c] text-[#a1a1aa] hover:text-white'
            }`}
            title="Voice Input"
          >
            <Mic className="w-4 h-4" />
          </button>

          <button
            onClick={handleSubmit}
            disabled={!prompt.trim()}
            className={`p-2 rounded-lg font-bold font-mono text-xs flex items-center justify-center transition-all cursor-pointer ${
              prompt.trim()
                ? 'bg-[#36f4a4] hover:bg-[#2de097] text-black shadow-md shadow-[#36f4a4]/10 active:scale-95'
                : 'bg-[#061a1c] text-[#4c5c5c] cursor-not-allowed'
            }`}
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
