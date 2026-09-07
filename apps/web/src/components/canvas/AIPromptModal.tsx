// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/components/canvas/AIPromptModal.tsx"
// purpose: "AI Prompt Modal and Style Selector for FLUX.1 + LayerDiffuse Layer Synthesis in Canvas Studio."
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

import React, { useState, useEffect } from 'react';
import type { AIGenerateLayerOptions } from '../../canvas/ai/types';

export interface StylePresetOption {
  id: string;
  label: string;
  icon: string;
  description: string;
  promptSuffix?: string;
  negativePrompt?: string;
}

export const STYLE_PRESETS: StylePresetOption[] = [
  {
    id: 'photorealistic',
    label: 'Photorealistic',
    icon: '📷',
    description: 'High-fidelity 8k studio product photography, clean lighting',
    promptSuffix: 'photorealistic, 8k resolution, detailed studio lighting, ray tracing',
    negativePrompt: 'blurry, distorted, low quality, artifacts, CGI cartoon',
  },
  {
    id: 'cyberpunk',
    label: 'Cyberpunk',
    icon: '🌆',
    description: 'Neon glow, futuristic metallic accents, high-contrast city vibe',
    promptSuffix: 'cyberpunk aesthetic, neon lighting, volumetric glow, octane render',
    negativePrompt: 'rustic, pastel, washed out, low contrast',
  },
  {
    id: 'ecommerce',
    label: 'E-Commerce',
    icon: '🛍️',
    description: 'Crisp commercial catalog display, pristine presentation',
    promptSuffix: 'commercial product photography, isolated studio backdrop, softbox lighting',
    negativePrompt: 'messy background, text, watermark, bad lighting',
  },
  {
    id: 'artistic',
    label: 'Artistic',
    icon: '🎨',
    description: 'Vibrant digital art, dynamic brush strokes, expressive palettes',
    promptSuffix: 'digital art, artistic concept, masterpiece, detailed textures',
    negativePrompt: 'photo, realistic, low effort',
  },
  {
    id: 'minimalist',
    label: 'Minimal',
    icon: '✨',
    description: 'Clean geometry, spacious composition, subtle monochromatic tones',
    promptSuffix: 'minimalist design, clean background, elegant composition, subtle shadows',
    negativePrompt: 'cluttered, overcrowded, noisy, complex patterns',
  },
];

export interface DimensionOption {
  label: string;
  width: number;
  height: number;
  aspectRatio: string;
}

export const DIMENSION_OPTIONS: DimensionOption[] = [
  { label: 'Square (1:1)', width: 512, height: 512, aspectRatio: '1:1' },
  { label: 'HD Square (1:1)', width: 1024, height: 1024, aspectRatio: '1:1' },
  { label: 'Landscape (16:9)', width: 1024, height: 576, aspectRatio: '16:9' },
  { label: 'Portrait (9:16)', width: 576, height: 1024, aspectRatio: '9:16' },
  { label: 'Banner (21:9)', width: 1024, height: 438, aspectRatio: '21:9' },
];

export const DIMENSION_PRESETS = DIMENSION_OPTIONS;


export interface AIPromptModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (prompt: string, options: Partial<AIGenerateLayerOptions>) => Promise<void> | void;
  isProcessing?: boolean;
  initialPrompt?: string;
  targetLayerId?: string;
}

export const AIPromptModal: React.FC<AIPromptModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isProcessing = false,
  initialPrompt = '',
  targetLayerId,
}) => {
  const [prompt, setPrompt] = useState(initialPrompt);
  const [negativePrompt, setNegativePrompt] = useState('');
  const [selectedStyle, setSelectedStyle] = useState<string>('photorealistic');
  const [selectedDimensionIndex, setSelectedDimensionIndex] = useState<number>(0);
  const [transparentBackground, setTransparentBackground] = useState<boolean>(true);
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);

  useEffect(() => {
    if (isOpen) {
      setPrompt(initialPrompt);
    }
  }, [isOpen, initialPrompt]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !isProcessing) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isProcessing, onClose]);

  if (!isOpen) return null;

  const currentDimension = DIMENSION_OPTIONS[selectedDimensionIndex] || DIMENSION_OPTIONS[0];

  const handlePresetSelect = (preset: StylePresetOption) => {
    setSelectedStyle(preset.id);
    if (preset.negativePrompt && !negativePrompt) {
      setNegativePrompt(preset.negativePrompt);
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isProcessing) return;

    const preset = STYLE_PRESETS.find((p) => p.id === selectedStyle);
    const finalPrompt = preset?.promptSuffix ? `${prompt.trim()}, ${preset.promptSuffix}` : prompt.trim();

    await onSubmit(finalPrompt, {
      negativePrompt: negativePrompt.trim() || preset?.negativePrompt,
      style: selectedStyle,
      width: currentDimension.width,
      height: currentDimension.height,
      transparentBackground,
      targetLayerId,
    });
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="ai-prompt-modal-title"
    >
      <div
        className="relative w-full max-w-2xl bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/80">
          <div className="flex items-center space-x-3">
            <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-indigo-500/20 text-indigo-400 text-lg">
              ✨
            </span>
            <div>
              <h2 id="ai-prompt-modal-title" className="text-lg font-semibold text-white">
                Generate Isolated AI Layer
              </h2>
              <p className="text-xs text-slate-400">
                Powered by FLUX.1 + LayerDiffuse Transparent Synthesis
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isProcessing}
            aria-label="Close modal"
            className="text-slate-400 hover:text-slate-200 transition-colors p-1.5 rounded-lg hover:bg-slate-800 disabled:opacity-50"
          >
            ✕
          </button>
        </div>

        {/* Modal Form Content */}
        <form onSubmit={handleGenerate} className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Prompt Textarea */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-slate-200">
              Prompt Description <span className="text-indigo-400">*</span>
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="E.g., Luxurious matte black cosmetic bottle on frosted glass pedestal..."
              rows={3}
              required
              disabled={isProcessing}
              className="w-full px-4 py-3 bg-slate-800/80 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all resize-none text-sm"
            />
            <div className="flex justify-between text-xs text-slate-500">
              <span>Be descriptive for best compositional results</span>
              <span>{prompt.length} chars</span>
            </div>
          </div>

          {/* 5 Style Pills */}
          <div className="space-y-2.5">
            <label className="block text-sm font-medium text-slate-200">
              Style Preset
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
              {STYLE_PRESETS.map((preset) => {
                const isSelected = selectedStyle === preset.id;
                return (
                  <button
                    key={preset.id}
                    type="button"
                    onClick={() => handlePresetSelect(preset)}
                    disabled={isProcessing}
                    title={preset.description}
                    className={`flex flex-col items-center justify-center p-3 rounded-xl border text-center transition-all ${
                      isSelected
                        ? 'bg-indigo-600/30 border-indigo-500 text-white shadow-lg shadow-indigo-500/10'
                        : 'bg-slate-800/50 border-slate-700/60 text-slate-300 hover:bg-slate-800 hover:border-slate-600'
                    }`}
                  >
                    <span className="text-2xl mb-1">{preset.icon}</span>
                    <span className="text-xs font-semibold">{preset.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Dimensions & Background Settings */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-200">
                Resolution & Aspect Ratio
              </label>
              <select
                value={selectedDimensionIndex}
                onChange={(e) => setSelectedDimensionIndex(Number(e.target.value))}
                disabled={isProcessing}
                className="w-full px-3 py-2.5 bg-slate-800/80 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {DIMENSION_OPTIONS.map((opt, idx) => (
                  <option key={opt.label} value={idx}>
                    {opt.label} ({opt.width}x{opt.height})
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-200">
                Layer Transparency
              </label>
              <label className="flex items-center space-x-3 px-3 py-2.5 bg-slate-800/80 border border-slate-700 rounded-xl cursor-pointer hover:bg-slate-800 transition-colors">
                <input
                  type="checkbox"
                  checked={transparentBackground}
                  onChange={(e) => setTransparentBackground(e.target.checked)}
                  disabled={isProcessing}
                  className="w-4 h-4 rounded text-indigo-600 bg-slate-700 border-slate-600 focus:ring-indigo-500"
                />
                <span className="text-sm text-slate-300 select-none">
                  Transparent Mask (LayerDiffuse)
                </span>
              </label>
            </div>
          </div>

          {/* Advanced Options Toggle */}
          <div className="border-t border-slate-800 pt-4">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-xs font-medium text-indigo-400 hover:text-indigo-300 flex items-center space-x-1"
            >
              <span>{showAdvanced ? '▼' : '▶'}</span>
              <span>Advanced AI Controls</span>
            </button>

            {showAdvanced && (
              <div className="mt-3 space-y-2 animate-fade-in">
                <label className="block text-xs font-medium text-slate-300">
                  Negative Prompt (Elements to avoid)
                </label>
                <input
                  type="text"
                  value={negativePrompt}
                  onChange={(e) => setNegativePrompt(e.target.value)}
                  placeholder="E.g., blurry, noisy, watermark, bad lighting..."
                  disabled={isProcessing}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-xs placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>
            )}
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-end space-x-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isProcessing}
              className="px-4 py-2.5 rounded-xl border border-slate-700 text-sm font-medium text-slate-300 hover:bg-slate-800 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!prompt.trim() || isProcessing}
              className="flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isProcessing ? (
                <>
                  <svg
                    className="animate-spin h-4 w-4 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8v8H4z"
                    />
                  </svg>
                  <span>Synthesizing Layer...</span>
                </>
              ) : (
                <>
                  <span>Generate Layer</span>
                  <span>✨</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
