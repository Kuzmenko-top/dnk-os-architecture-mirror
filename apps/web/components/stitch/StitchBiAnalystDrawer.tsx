// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/stitch/StitchBiAnalystDrawer.tsx"
// purpose: "Embedded AI Analyst & DuckDB Lakehouse intelligence drawer with NL2SQL reasoning and dynamic visual charts."
// canonical_source: true
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-09-06"
// author: "Antigravity (Mentor) & Gerych Prime"
// --- END DNK-MRH-HEADER ---

import React, { useState, useEffect } from 'react';

export interface AnalysisResult {
  question: string;
  reasoning_plan: string[];
  generated_sql: string;
  chart_type: 'bar' | 'line' | 'table';
  title: string;
  result: {
    columns: string[];
    rows: any[][];
    execution_time_ms: number;
    row_count: number;
    engine: string;
  };
}

export interface StitchBiAnalystDrawerProps {
  onNotification?: (msg: { text: string; type: 'success' | 'info' | 'warning' | 'error' }) => void;
  onClose?: () => void;
}

export const StitchBiAnalystDrawer: React.FC<StitchBiAnalystDrawerProps> = ({ onNotification, onClose }) => {
  const [queryText, setQueryText] = useState<string>('What is our total revenue by customer?');
  const [loading, setLoading] = useState<boolean>(false);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [activeTab, setActiveTab] = useState<'chart' | 'sql' | 'plan'>('chart');
  const [copied, setCopied] = useState<boolean>(false);

  // Auto-run initial query on mount
  useEffect(() => {
    handleRunQuery(queryText);
  }, []);

  const handleRunQuery = async (question: string) => {
    if (!question.trim()) return;
    setLoading(true);
    try {
      const res = await fetch('/api/v3/lakehouse/nl2sql', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      });
      if (!res.ok) throw new Error('Query execution failed');
      const data: AnalysisResult = await res.json();
      setAnalysis(data);
      if (onNotification) {
        onNotification({
          text: `DuckDB: Executed in ${data.result.execution_time_ms}ms (${data.result.row_count} rows)`,
          type: 'success'
        });
      }
    } catch (e: any) {
      if (onNotification) {
        onNotification({ text: `Analysis Error: ${e.message}`, type: 'error' });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCopySql = () => {
    if (analysis?.generated_sql) {
      navigator.clipboard.writeText(analysis.generated_sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const quickPrompts = [
    { label: '💰 Виручка за клієнтами', query: 'What is our total revenue by customer?' },
    { label: '⚡ Латентність та токени агентів', query: 'Show agent latency and token metrics' },
    { label: '📦 Останні замовлення Shopify', query: 'Show recent Shopify orders and amounts' }
  ];

  return (
    <div className="w-[620px] max-h-[560px] bg-slate-950/95 backdrop-blur-xl border border-slate-800/80 rounded-2xl shadow-2xl flex flex-col font-sans text-slate-200 overflow-hidden z-50 pointer-events-auto">
      {/* Header */}
      <div className="px-4 py-3 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs font-bold font-mono tracking-wider text-white">
            AI ANALYST • <span className="text-emerald-400">DuckDB Lakehouse</span>
          </span>
          <span className="px-2 py-0.5 text-[10px] font-mono bg-emerald-950/80 text-emerald-300 border border-emerald-800/50 rounded-full">
            In-Memory Columnar
          </span>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white text-xs font-mono px-2 py-1 rounded hover:bg-slate-800 transition-colors"
          >
            ✕
          </button>
        )}
      </div>

      {/* Query Bar */}
      <div className="p-4 border-b border-slate-800/60 flex flex-col gap-2.5">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleRunQuery(queryText);
          }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={queryText}
            onChange={(e) => setQueryText(e.target.value)}
            placeholder="Запитайте природною мовою (напр. 'Виручка за клієнтами')..."
            className="flex-1 px-3.5 py-2 text-xs bg-slate-900 border border-slate-700/80 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold text-xs rounded-xl shadow-lg transition-all disabled:opacity-50 cursor-pointer"
          >
            {loading ? 'Аналіз...' : 'Запитати ⚡'}
          </button>
        </form>

        {/* Quick prompt chips */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[10px] text-slate-500 font-mono">Підказки:</span>
          {quickPrompts.map((p, idx) => (
            <button
              key={idx}
              onClick={() => {
                setQueryText(p.query);
                handleRunQuery(p.query);
              }}
              className="px-2 py-0.5 bg-slate-900/80 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-[10px] text-slate-400 hover:text-white rounded-lg transition-all cursor-pointer"
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content Area */}
      {analysis && (
        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
          {/* Sub Navigation */}
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div className="flex gap-2">
              <button
                onClick={() => setActiveTab('chart')}
                className={`px-3 py-1 text-xs font-medium rounded-lg transition-all ${
                  activeTab === 'chart'
                    ? 'bg-indigo-600/30 text-indigo-300 border border-indigo-500/40'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                📊 Візуалізація ({analysis.chart_type})
              </button>
              <button
                onClick={() => setActiveTab('sql')}
                className={`px-3 py-1 text-xs font-medium rounded-lg transition-all ${
                  activeTab === 'sql'
                    ? 'bg-indigo-600/30 text-indigo-300 border border-indigo-500/40'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                🔍 SQL & Джерело
              </button>
              <button
                onClick={() => setActiveTab('plan')}
                className={`px-3 py-1 text-xs font-medium rounded-lg transition-all ${
                  activeTab === 'plan'
                    ? 'bg-indigo-600/30 text-indigo-300 border border-indigo-500/40'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                🧠 План міркувань (4 кроки)
              </button>
            </div>
            <span className="text-[10px] font-mono text-slate-500">
              {analysis.result.execution_time_ms} ms • {analysis.result.row_count} рядків
            </span>
          </div>

          {/* TAB 1: Chart / Table View */}
          {activeTab === 'chart' && (
            <div className="flex flex-col gap-3">
              <div className="text-xs font-bold text-slate-100">{analysis.title}</div>
              
              {/* Dynamic Bar Chart Render */}
              {analysis.chart_type === 'bar' && (
                <div className="bg-slate-900/90 border border-slate-800/80 p-4 rounded-xl flex flex-col gap-3">
                  {analysis.result.rows.map((row, idx) => {
                    const label = String(row[0]);
                    const value = Number(row[1]) || 0;
                    const maxVal = Math.max(...analysis.result.rows.map(r => Number(r[1]) || 1));
                    const pct = Math.round((value / maxVal) * 100);
                    return (
                      <div key={idx} className="flex flex-col gap-1">
                        <div className="flex justify-between text-[11px] font-mono">
                          <span className="text-slate-300 font-semibold">{label}</span>
                          <span className="text-emerald-400 font-bold">${value.toFixed(2)}</span>
                        </div>
                        <div className="w-full bg-slate-800/80 h-3 rounded-full overflow-hidden p-0.5">
                          <div
                            className="bg-gradient-to-r from-cyan-500 to-indigo-500 h-full rounded-full transition-all duration-500"
                            style={{ width: `${Math.max(pct, 8)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Dynamic Line / Metrics Render */}
              {analysis.chart_type === 'line' && (
                <div className="grid grid-cols-3 gap-2.5">
                  {analysis.result.rows.map((row, idx) => (
                    <div key={idx} className="bg-slate-900/90 border border-slate-800 p-3 rounded-xl flex flex-col gap-1">
                      <span className="text-[10px] font-mono text-slate-400 uppercase">{String(row[0])}</span>
                      <span className="text-lg font-bold font-mono text-cyan-400">
                        {Number(row[1]).toFixed(1)} ms
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {row[2]} токенів
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* Dynamic Table Render */}
              {analysis.chart_type === 'table' && (
                <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-x-auto">
                  <table className="w-full text-left text-[11px] font-mono">
                    <thead className="bg-slate-800/60 text-slate-400 border-b border-slate-800">
                      <tr>
                        {analysis.result.columns.map((c, i) => (
                          <th key={i} className="px-3 py-2">{c}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-slate-200">
                      {analysis.result.rows.map((row, rIdx) => (
                        <tr key={rIdx} className="hover:bg-slate-800/30">
                          {row.map((cell, cIdx) => (
                            <td key={cIdx} className="px-3 py-1.5">{String(cell)}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: Generated SQL */}
          {activeTab === 'sql' && (
            <div className="flex flex-col gap-2">
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold text-slate-300">DuckDB SQL Statement</span>
                <button
                  onClick={handleCopySql}
                  className="text-[11px] font-mono px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-all"
                >
                  {copied ? 'Скопійовано! ✓' : 'Копіювати SQL'}
                </button>
              </div>
              <pre className="p-3 bg-slate-900 border border-slate-800 rounded-xl text-[11px] font-mono text-cyan-300 overflow-x-auto whitespace-pre-wrap leading-relaxed">
                {analysis.generated_sql}
              </pre>
            </div>
          )}

          {/* TAB 3: Reasoning Plan */}
          {activeTab === 'plan' && (
            <div className="flex flex-col gap-2">
              <span className="text-xs font-bold text-slate-300">AI Analyst Reasoning DAG</span>
              <div className="flex flex-col gap-2 bg-slate-900/80 border border-slate-800 p-3 rounded-xl">
                {analysis.reasoning_plan.map((step, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs font-mono text-slate-300">
                    <span className="w-5 h-5 rounded-full bg-indigo-950 border border-indigo-800 text-indigo-400 flex items-center justify-center text-[10px] font-bold shrink-0">
                      {idx + 1}
                    </span>
                    <span className="leading-5">{step}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default StitchBiAnalystDrawer;
