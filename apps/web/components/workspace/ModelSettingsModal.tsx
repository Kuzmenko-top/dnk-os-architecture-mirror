// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_workspace_ModelSettingsModal"
// purpose: "Model Provider Hub & Project Configuration Modal for DNK OS Studio Workspace (Gemini, Claude, OpenAI, Shopify & ElevenLabs)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-31"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { 
  X, 
  Cpu, 
  Key, 
  Sliders, 
  Sparkles, 
  Check, 
  ShieldCheck, 
  ShoppingBag, 
  Volume2, 
  Globe,
  Database,
  Save,
  Server
} from 'lucide-react';

interface ModelSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentModel?: string;
  onSaveModel?: (modelId: string, settings: any) => void;
}

const AVAILABLE_MODELS = [
  {
    id: 'gemini-2.5-pro',
    name: 'Gemini 2.5 Pro (Vertex AI)',
    provider: 'Google Cloud',
    speed: 'Ultra Fast',
    context: '2M Tokens',
    badge: 'Recommended',
    description: 'Premier multi-modal model for TaskDNA decomposition, Shopify Liquid generation, and real-time AST synthesis.'
  },
  {
    id: 'claude-3-5-sonnet',
    name: 'Claude 3.5 Sonnet',
    provider: 'Anthropic',
    speed: 'High Speed',
    context: '200k Tokens',
    badge: 'Code Specialist',
    description: 'Exceptional precision for complex Liquid AST compilation, React component refactoring, and fail-closed audit.'
  },
  {
    id: 'gpt-4o',
    name: 'GPT-4o Omnichannel',
    provider: 'OpenAI',
    speed: 'Fast',
    context: '128k Tokens',
    badge: 'Creative & Marketing',
    description: 'High-converting ad copywriting, TikTok/Reels UGC scripts, and SEO blog composition.'
  },
  {
    id: 'local-vllm-qwen',
    name: 'Qwen 2.5 Coder 32B (Local vLLM)',
    provider: 'Self-Hosted / Local',
    speed: 'Local GPU',
    context: '32k Tokens',
    badge: 'Zero Cloud Cost',
    description: 'Privacy-first offline local LLM worker connected via local OpenAI-compatible endpoint.'
  }
];

export default function ModelSettingsModal({
  isOpen,
  onClose,
  currentModel = 'gemini-2.5-pro',
  onSaveModel
}: ModelSettingsModalProps) {
  const [selectedModel, setSelectedModel] = useState(currentModel);
  const [activeTab, setActiveTab] = useState<'models' | 'keys' | 'project'>('models');
  
  const [apiKeys, setApiKeys] = useState({
    vertexKey: '••••••••••••••••••••••••••••••••',
    anthropicKey: '',
    openaiKey: '',
    elevenLabsKey: '',
    shopifyToken: ''
  });

  const [projectConfig, setProjectConfig] = useState({
    projectName: 'ReBurn Bio-Smoker 3.0 Launch',
    storeDomain: 'reburn-smokers.myshopify.com',
    toneOfVoice: 'Premium High-Tech & Minimalist Outdoor',
    primaryColor: '#00dc82'
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fadeIn select-none">
      <div className="w-full max-w-2xl bg-[#0e111a] border border-white/10 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        
        {/* Modal Header */}
        <div className="p-5 border-b border-white/10 flex items-center justify-between bg-[#121624]">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-[#00dc82]/10 border border-[#00dc82]/30 flex items-center justify-center text-[#00dc82]">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white tracking-tight">Studio Workspace & Model Settings</h2>
              <p className="text-xs text-slate-400">Configure LLM providers, API credentials, and project identity</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 px-5 pt-3 border-b border-white/5 bg-[#101320] text-xs">
          <button
            onClick={() => setActiveTab('models')}
            className={`pb-2.5 px-2 font-semibold transition-all border-b-2 flex items-center gap-1.5 ${
              activeTab === 'models'
                ? 'border-[#00dc82] text-[#00dc82]'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Cpu className="w-3.5 h-3.5" />
            <span>LLM Models ({AVAILABLE_MODELS.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('keys')}
            className={`pb-2.5 px-2 font-semibold transition-all border-b-2 flex items-center gap-1.5 ${
              activeTab === 'keys'
                ? 'border-[#00dc82] text-[#00dc82]'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Key className="w-3.5 h-3.5" />
            <span>API Credentials</span>
          </button>

          <button
            onClick={() => setActiveTab('project')}
            className={`pb-2.5 px-2 font-semibold transition-all border-b-2 flex items-center gap-1.5 ${
              activeTab === 'project'
                ? 'border-[#00dc82] text-[#00dc82]'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>Project Identity</span>
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 overflow-y-auto flex-1 space-y-4">
          
          {/* TAB 1: MODELS */}
          {activeTab === 'models' && (
            <div className="space-y-3">
              {AVAILABLE_MODELS.map((model) => {
                const isSelected = selectedModel === model.id;
                return (
                  <div
                    key={model.id}
                    onClick={() => setSelectedModel(model.id)}
                    className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-[#00dc82]/10 border-[#00dc82] shadow-lg shadow-emerald-500/10'
                        : 'bg-[#121624]/60 border-white/5 hover:border-white/20 hover:bg-[#121624]'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-white">{model.name}</span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white/10 text-slate-300">
                          {model.provider}
                        </span>
                        {model.badge && (
                          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[#00dc82]/20 text-[#00dc82] border border-[#00dc82]/40">
                            {model.badge}
                          </span>
                        )}
                      </div>
                      <div className={`w-5 h-5 rounded-full flex items-center justify-center border ${
                        isSelected ? 'bg-[#00dc82] border-[#00dc82] text-black font-bold' : 'border-slate-700'
                      }`}>
                        {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                      </div>
                    </div>
                    <p className="text-xs text-slate-400 mb-2 leading-relaxed">{model.description}</p>
                    <div className="flex items-center gap-4 text-[11px] font-mono text-slate-500">
                      <span>Speed: <strong className="text-slate-300">{model.speed}</strong></span>
                      <span>Context: <strong className="text-slate-300">{model.context}</strong></span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* TAB 2: API KEYS */}
          {activeTab === 'keys' && (
            <div className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5 mb-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-[#00dc82]" />
                  Google Cloud Vertex AI Key / Project ID
                </label>
                <input
                  type="password"
                  value={apiKeys.vertexKey}
                  onChange={(e) => setApiKeys({ ...apiKeys, vertexKey: e.target.value })}
                  placeholder="AIzaSy..."
                  className="w-full p-2.5 rounded-xl bg-[#121624] border border-white/10 text-xs text-white focus:outline-none focus:border-[#00dc82] font-mono"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5 mb-1.5">
                  <ShoppingBag className="w-3.5 h-3.5 text-emerald-400" />
                  Shopify Admin Access Token
                </label>
                <input
                  type="password"
                  value={apiKeys.shopifyToken}
                  onChange={(e) => setApiKeys({ ...apiKeys, shopifyToken: e.target.value })}
                  placeholder="shpat_..."
                  className="w-full p-2.5 rounded-xl bg-[#121624] border border-white/10 text-xs text-white focus:outline-none focus:border-[#00dc82] font-mono"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5 mb-1.5">
                  <Volume2 className="w-3.5 h-3.5 text-pink-400" />
                  ElevenLabs Voice Synthesis API Key
                </label>
                <input
                  type="password"
                  value={apiKeys.elevenLabsKey}
                  onChange={(e) => setApiKeys({ ...apiKeys, elevenLabsKey: e.target.value })}
                  placeholder="xi_..."
                  className="w-full p-2.5 rounded-xl bg-[#121624] border border-white/10 text-xs text-white focus:outline-none focus:border-[#00dc82] font-mono"
                />
              </div>
            </div>
          )}

          {/* TAB 3: PROJECT IDENTITY */}
          {activeTab === 'project' && (
            <div className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">Project Workspace Name</label>
                <input
                  type="text"
                  value={projectConfig.projectName}
                  onChange={(e) => setProjectConfig({ ...projectConfig, projectName: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-[#121624] border border-white/10 text-xs text-white focus:outline-none focus:border-[#00dc82]"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">Connected Shopify Domain</label>
                <input
                  type="text"
                  value={projectConfig.storeDomain}
                  onChange={(e) => setProjectConfig({ ...projectConfig, storeDomain: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-[#121624] border border-white/10 text-xs text-white focus:outline-none focus:border-[#00dc82] font-mono"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">Brand Tone of Voice</label>
                <textarea
                  value={projectConfig.toneOfVoice}
                  onChange={(e) => setProjectConfig({ ...projectConfig, toneOfVoice: e.target.value })}
                  rows={2}
                  className="w-full p-2.5 rounded-xl bg-[#121624] border border-white/10 text-xs text-white focus:outline-none focus:border-[#00dc82] resize-none"
                />
              </div>
            </div>
          )}

        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-white/10 flex items-center justify-between bg-[#121624]">
          <span className="text-[11px] text-slate-500 font-mono flex items-center gap-1">
            <Server className="w-3 h-3 text-[#00dc82]" /> SCONES L3 Vault Encrypted
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-white/5 transition-all"
            >
              Cancel
            </button>
            <button
              onClick={() => {
                onSaveModel?.(selectedModel, { apiKeys, projectConfig });
                onClose();
              }}
              className="px-4 py-2 rounded-xl bg-[#00dc82] hover:bg-[#00c574] text-black font-bold text-xs flex items-center gap-1.5 shadow-md shadow-emerald-500/20 transition-all cursor-pointer"
            >
              <Save className="w-3.5 h-3.5" />
              <span>Save & Apply</span>
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
