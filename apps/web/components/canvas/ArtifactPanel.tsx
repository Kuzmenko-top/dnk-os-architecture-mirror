// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_ArtifactPanel"
// purpose: "Artifact Panel component with Markdown viewer, Security Gate safeguards, and 1-Click GitHub PR Generator"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-08-29"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Edit3, 
  Check, 
  Copy, 
  ShieldAlert, 
  Sparkles, 
  Save, 
  X, 
  Code2, 
  Download,
  GitPullRequest,
  ExternalLink,
  GitBranch
} from 'lucide-react';

interface ArtifactPanelProps {
  canvasId: string;
  artifactData: any;
  onUpdate: (updatedData: any) => void;
}

export default function ArtifactPanel({ canvasId, artifactData, onUpdate }: ArtifactPanelProps) {
  const [content, setContent] = useState(artifactData?.content || '');
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeployingPR, setIsDeployingPR] = useState(false);
  const [prResult, setPrResult] = useState<{ pr_url: string; branch: string } | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (artifactData?.content !== undefined) {
      setContent(artifactData.content);
    }
  }, [artifactData]);

  const handleCopy = () => {
    if (!content) return;
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!content) return;
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `artifact-${canvasId}.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleDeployPR = async () => {
    if (!content) return;
    setIsDeployingPR(true);
    setError(null);
    setPrResult(null);
    try {
      const res = await fetch('/api/agent/deploy/pr', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          canvas_id: canvasId,
          title: `Feat(Canvas): Autonomous Artifact Update #${canvasId.slice(0, 8)}`,
          description: `Auto-generated production artifact compiled via DNK OS Visual Shell.\n\n### Summary\n${content.slice(0, 300)}...`,
          content: content
        })
      });

      const data = await res.json();
      if (res.ok && data.success) {
        setPrResult({ pr_url: data.pr_url, branch: data.branch });
      } else {
        setError(data.detail || 'Не вдалося створити Pull Request.');
      }
    } catch (e: any) {
      setError(`Збій створення PR: ${e.message}`);
    } finally {
      setIsDeployingPR(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError(null);
    try {
      const res = await fetch(`/api/artifact/${canvasId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        if (data.error_type === 'SecurityGateDenied' || res.status === 403) {
          setError(`🚨 Security Gate Denied: ${data.detail || 'Risky action blocked by system governance policy.'}`);
        } else {
          setError(data.detail || 'Невідома помилка оновлення артефакту.');
        }
      } else {
        onUpdate(data);
        setIsEditing(false);
      }
    } catch (e: any) {
      setError(`Помилка запиту: ${e.message || e}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-900/90 backdrop-blur-xl border border-slate-800/80 rounded-2xl p-6 text-white shadow-2xl relative overflow-hidden">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4 border-b border-slate-800/80 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-blue-500/20 to-cyan-500/20 border border-blue-500/30 text-cyan-400">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              Панель Артефакту
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                SOTA GenAI
              </span>
            </h3>
            <p className="text-xs text-slate-400">Результати автономного дослідження та генерації коду</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {content && (
            <>
              <button
                onClick={handleDeployPR}
                disabled={isDeployingPR}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-xs font-bold text-white shadow-md shadow-emerald-600/20 transition-all cursor-pointer disabled:opacity-50"
                title="1-Click Pull Request"
              >
                {isDeployingPR ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Створення PR...</span>
                  </>
                ) : (
                  <>
                    <GitPullRequest className="w-3.5 h-3.5" />
                    <span>Створити PR</span>
                  </>
                )}
              </button>
              <button
                onClick={handleCopy}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/60 text-xs font-medium text-slate-300 hover:text-white transition-all cursor-pointer"
                title="Скопіювати артефакт"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                {copied ? 'Скопійовано' : 'Копіювати'}
              </button>
              <button
                onClick={handleDownload}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/60 text-xs font-medium text-slate-300 hover:text-white transition-all cursor-pointer"
                title="Завантажити Markdown"
              >
                <Download className="w-3.5 h-3.5" /> MD
              </button>
            </>
          )}

          {isEditing ? (
            <div className="flex items-center gap-2">
              <button
                onClick={() => { setIsEditing(false); setContent(artifactData?.content || ''); setError(null); }}
                className="flex items-center gap-1 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl text-xs font-medium transition-all cursor-pointer"
              >
                <X className="w-3.5 h-3.5" /> Скасувати
              </button>
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="flex items-center gap-1.5 px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 active:scale-95 disabled:opacity-50 transition-all rounded-xl text-xs font-semibold shadow-md cursor-pointer"
              >
                <Save className="w-3.5 h-3.5" />
                {isSaving ? 'Збереження...' : 'Зберегти'}
              </button>
            </div>
          ) : (
            <button
              onClick={() => setIsEditing(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/60 rounded-xl text-xs font-medium text-slate-200 hover:text-white transition-all cursor-pointer"
            >
              <Edit3 className="w-3.5 h-3.5" /> Редагувати
            </button>
          )}
        </div>
      </div>

      {/* PR Result Banner */}
      {prResult && (
        <div className="mb-4 p-3 bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 text-xs rounded-xl flex items-center justify-between animate-in fade-in duration-200">
          <div className="flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-emerald-400" />
            <span>Створено PR у гілці <strong>{prResult.branch}</strong></span>
          </div>
          <a
            href={prResult.pr_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 font-bold text-cyan-300 hover:text-cyan-200 underline"
          >
            <span>Переглянути PR</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      )}

      {/* Error alert */}
      {error && (
        <div className="mb-4 p-3.5 bg-rose-950/60 border border-rose-500/40 text-rose-300 text-xs rounded-xl flex items-center gap-2.5 animate-in fade-in duration-200">
          <ShieldAlert className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Content Viewport */}
      <div className="relative flex-grow border border-slate-800/80 bg-slate-950/70 rounded-2xl overflow-y-auto p-5 min-h-[260px]">
        {isEditing ? (
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="w-full h-full min-h-[220px] bg-transparent text-slate-200 font-mono text-xs focus:outline-none resize-none leading-relaxed"
            placeholder="Введіть вміст артефакту (Markdown)..."
          />
        ) : content ? (
          <div className="prose prose-invert max-w-none text-xs leading-relaxed font-sans text-slate-200">
            <pre className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 font-mono text-xs text-indigo-300 whitespace-pre-wrap">
              {content}
            </pre>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full min-h-[200px] text-center text-slate-500 gap-3">
            <div className="p-3 rounded-2xl bg-slate-900 border border-slate-800">
              <Sparkles className="w-6 h-6 text-slate-600" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-400">Артефакт поки що пустий</p>
              <p className="text-xs text-slate-500 mt-0.5">Натисніть «🤖 Запустити Сценарій» зверху для автоматичної генерації або відредагуйте вручну.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
