// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/stitch/StitchTaskForestDrawer.tsx"
// purpose: "Task Forest 5-Plant Scale Engine Spatial HQ Inspector, Tree Explorer, Genetic Inspector and Time-Travel Scrubber."
// canonical_source: true
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-09-06"
// author: "Antigravity (Mentor) & Gerych Prime"
// --- END DNK-MRH-HEADER ---

import React, { useState, useEffect } from 'react';

interface PlantNode {
  id: string;
  title: string;
  plant_scale: 'field' | 'sector' | 'tree' | 'bush' | 'flower';
  status: 'todo' | 'pending' | 'in_progress' | 'completed' | 'cancelled' | 'ready';
  progress: number;
  parent_id?: string | null;
  assigned_agent?: string | null;
  weight: number;
  git_diff?: string | null;
  dto_contract?: any | null;
  verification_status?: string | null;
  author?: string | null;
  updated_at?: string | null;
  children: PlantNode[];
}

interface MutationEvent {
  event_id: string;
  timestamp: string;
  node_id: string;
  node_title: string;
  mutation_type: 'create' | 'update';
  previous_status: string;
  new_status: string;
  previous_progress: number;
  new_progress: number;
  overall_field_progress: number;
  snapshot?: Record<string, any>;
}

export interface StitchTaskForestDrawerProps {
  onNotification?: (msg: { text: string; type: 'success' | 'info' | 'warning' | 'error' }) => void;
  onClose?: () => void;
}

export const StitchTaskForestDrawer: React.FC<StitchTaskForestDrawerProps> = ({ onNotification, onClose }) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [nodesMap, setNodesMap] = useState<Record<string, PlantNode>>({});
  const [rootField, setRootField] = useState<PlantNode | null>(null);
  const [overallProgress, setOverallProgress] = useState<number>(88);
  const [scaleCounts, setScaleCounts] = useState<Record<string, number>>({});
  
  const [selectedNode, setSelectedNode] = useState<PlantNode | null>(null);
  const [historyEvents, setHistoryEvents] = useState<MutationEvent[]>([]);
  const [historySliderVal, setHistorySliderValue] = useState<number>(0);
  const [collapsedNodes, setCollapsedNodes] = useState<Record<string, boolean>>({});
  
  // Create / Mutation Form States
  const [isAddingNode, setIsAddingNode] = useState<boolean>(false);
  const [newTitle, setNewTitle] = useState<string>('');
  const [newAgent, setNewAgent] = useState<string>('gerych_builder');
  const [newScale, setNewScale] = useState<'flower' | 'bush'>('flower');
  const [newParentId, setNewParentId] = useState<string>('bush-004');

  // Load baseline Task Forest graph and evolution history
  const fetchGraph = async () => {
    try {
      const res = await fetch('/api/v3/task_forest/graph');
      if (!res.ok) throw new Error('Failed to fetch Task Forest graph');
      const data = await res.json();
      setRootField(data.root_field);
      setNodesMap(data.nodes);
      setOverallProgress(data.overall_progress);
      setScaleCounts(data.scale_counts);
      
      // Keep selected node up to date
      if (selectedNode) {
        const updated = data.nodes[selectedNode.id];
        if (updated) setSelectedNode(updated);
      }
    } catch (err: any) {
      console.error(err);
      if (onNotification) {
        onNotification({ text: 'Error loading Task Forest graph', type: 'error' });
      }
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await fetch('/api/v3/task_forest/evolution_history');
      if (!res.ok) throw new Error('Failed to fetch Task Forest history');
      const data = await res.json();
      setHistoryEvents(data.events || []);
      setHistorySliderValue((data.events || []).length);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await Promise.all([fetchGraph(), fetchHistory()]);
      setLoading(false);
    };
    init();
  }, []);

  // Time-Travel Scrubber Action
  const handleScrubberChange = (val: number) => {
    setHistorySliderValue(val);
    if (val === historyEvents.length) {
      // Restore live view
      fetchGraph();
      if (onNotification) {
        onNotification({ text: 'Restored to Live Real-time Task Forest', type: 'info' });
      }
      return;
    }

    const event = historyEvents[val - 1];
    if (event && event.snapshot) {
      const snapshot = event.snapshot;
      // Re-hydrate state from snapshot
      setRootField(snapshot.root_field);
      setNodesMap(snapshot.nodes);
      setOverallProgress(snapshot.overall_progress);
      setScaleCounts(snapshot.scale_counts);
      if (onNotification) {
        onNotification({ 
          text: `Time-Travel: Viewing state as of ${new Date(event.timestamp).toLocaleTimeString()}`, 
          type: 'info' 
        });
      }
    }
  };

  // Node Mutation Trigger
  const handleMutateNode = async (nodeId: string, status: string, progress: number) => {
    try {
      const res = await fetch('/api/v3/task_forest/node/mutate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          node_id: nodeId,
          status,
          progress
        })
      });
      if (!res.ok) throw new Error('Mutation request failed');
      const data = await res.json();
      
      if (onNotification) {
        onNotification({ 
          text: `Task Forest mutated: ${data.node.title} -> ${data.node.status} (${data.node.progress}%)`, 
          type: 'success' 
        });
      }
      
      await Promise.all([fetchGraph(), fetchHistory()]);
    } catch (err) {
      if (onNotification) {
        onNotification({ text: 'Failed to mutate task node', type: 'error' });
      }
    }
  };

  // Create New Node (Flower or Bush)
  const handleCreateNode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    try {
      const res = await fetch('/api/v3/task_forest/node/mutate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          parent_id: newParentId,
          title: newTitle,
          plant_scale: newScale,
          assigned_agent: newAgent,
          status: 'todo',
          progress: 0
        })
      });
      if (!res.ok) throw new Error('Node creation failed');
      const data = await res.json();
      
      if (onNotification) {
        onNotification({ text: `Created new 🌸 Flower: ${data.node.title} under ${nodesMap[newParentId]?.title || newParentId}`, type: 'success' });
      }
      
      setNewTitle('');
      setIsAddingNode(false);
      await Promise.all([fetchGraph(), fetchHistory()]);
    } catch (err) {
      if (onNotification) {
        onNotification({ text: 'Failed to add node', type: 'error' });
      }
    }
  };

  const toggleCollapse = (id: string) => {
    setCollapsedNodes(prev => ({ ...prev, [id]: !prev[id] }));
  };

  // Helper colors and icons
  const getScaleIcon = (scale: string) => {
    switch (scale) {
      case 'field': return '🌾';
      case 'sector': return '🏞️';
      case 'tree': return '🌳';
      case 'bush': return '🌿';
      case 'flower': return '🌸';
      default: return '🌱';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
      case 'in_progress': return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
      case 'pending': return 'text-sky-400 bg-sky-500/10 border-sky-500/30';
      case 'ready': return 'text-indigo-400 bg-indigo-500/10 border-indigo-500/30';
      case 'cancelled': return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
      default: return 'text-gray-400 bg-gray-500/10 border-gray-500/30';
    }
  };

  const getStatusDot = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-emerald-500';
      case 'in_progress': return 'bg-amber-500';
      case 'pending': return 'bg-sky-500';
      case 'ready': return 'bg-indigo-500';
      case 'cancelled': return 'bg-rose-500';
      default: return 'bg-gray-500';
    }
  };

  // Recursive Tree Node Renderer
  const renderTreeNode = (node: PlantNode, depth: number = 0) => {
    const isCollapsed = collapsedNodes[node.id];
    const hasChildren = node.children && node.children.length > 0;
    const isSelected = selectedNode?.id === node.id;
    
    return (
      <div key={node.id} className="flex flex-col select-none">
        <div 
          className={`group flex items-center justify-between p-2 rounded-lg border transition-all cursor-pointer mb-1 ${
            isSelected 
              ? 'border-indigo-500 bg-indigo-500/15 text-white' 
              : 'border-slate-800/60 bg-slate-900/40 hover:bg-slate-800/40 hover:border-slate-700/80 text-slate-300'
          }`}
          style={{ marginLeft: `${depth * 14}px` }}
          onClick={() => setSelectedNode(node)}
        >
          <div className="flex items-center space-x-2 overflow-hidden mr-2">
            {hasChildren ? (
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  toggleCollapse(node.id);
                }}
                className="p-0.5 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
              >
                <span className="text-[10px] block transform transition-transform" style={{ transform: isCollapsed ? 'rotate(-90deg)' : 'rotate(0deg)' }}>
                  ▼
                </span>
              </button>
            ) : (
              <span className="w-3" />
            )}
            
            <span className="text-sm">{getScaleIcon(node.plant_scale)}</span>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 text-[9px] bg-slate-850 px-1 py-0.5 rounded border border-slate-800/80">
              {node.plant_scale}
            </span>
            <span className="text-xs font-medium truncate">{node.title}</span>
          </div>

          <div className="flex items-center space-x-3 shrink-0">
            {/* Tiny Progress Indicator */}
            <div className="flex items-center space-x-1.5">
              <div className="w-12 h-1.5 bg-slate-950 rounded-full overflow-hidden border border-slate-800/60">
                <div 
                  className={`h-full transition-all duration-300 ${
                    node.progress === 100 ? 'bg-emerald-500' : 'bg-indigo-500'
                  }`} 
                  style={{ width: `${node.progress}%` }} 
                />
              </div>
              <span className="text-[10px] font-bold text-slate-400 w-7 text-right">
                {Math.round(node.progress)}%
              </span>
            </div>

            {/* Status dot */}
            <span className={`w-2 h-2 rounded-full ${getStatusDot(node.status)}`} title={node.status} />
          </div>
        </div>

        {hasChildren && !isCollapsed && (
          <div className="flex flex-col">
            {node.children.map(child => renderTreeNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="fixed right-4 top-[84px] bottom-4 w-[540px] bg-slate-950/95 backdrop-blur-xl border border-slate-800/80 rounded-2xl shadow-2xl flex flex-col overflow-hidden z-50 transition-all duration-300 transform animate-in slide-in-from-right-8">
      {/* Header */}
      <div className="p-4 border-b border-slate-800/80 flex items-center justify-between bg-slate-900/40">
        <div className="flex items-center space-x-2.5">
          <span className="text-xl">🌲</span>
          <div>
            <h2 className="text-sm font-bold text-white tracking-wide">TASK FOREST SPATIAL HQ</h2>
            <p className="text-[10px] text-slate-400 font-mono">TASK-DNK-TASK-FOREST-SPATIAL-HQ-005</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Add node trigger */}
          <button 
            onClick={() => setIsAddingNode(!isAddingNode)}
            className="px-2.5 py-1 text-[11px] font-semibold bg-indigo-600 hover:bg-indigo-500 text-white rounded-md border border-indigo-500/40 transition-colors flex items-center space-x-1"
          >
            <span>+</span> <span>Add Plant</span>
          </button>
          
          {onClose && (
            <button 
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-slate-800/80 text-slate-400 hover:text-slate-200 transition-colors border border-transparent hover:border-slate-700/40"
            >
              <span className="text-xs">✕</span>
            </button>
          )}
        </div>
      </div>

      {/* Progress Rollup Dashboard */}
      <div className="p-4 bg-slate-900/20 border-b border-slate-800/60 grid grid-cols-3 gap-3">
        <div className="bg-slate-900/60 border border-slate-800/60 rounded-xl p-2.5 flex flex-col justify-between">
          <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Field Rollup</span>
          <div className="flex items-baseline space-x-1.5 mt-1">
            <span className="text-xl font-black text-emerald-400">{Math.round(overallProgress)}%</span>
            <span className="text-[10px] text-emerald-500/80">🌾 Field</span>
          </div>
          <div className="w-full h-1 bg-slate-950 rounded-full mt-2 overflow-hidden">
            <div className="h-full bg-emerald-500" style={{ width: `${overallProgress}%` }} />
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/60 rounded-xl p-2.5 flex flex-col justify-between">
          <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Forest Size</span>
          <div className="flex items-baseline space-x-1.5 mt-1">
            <span className="text-xl font-black text-white">{Object.keys(nodesMap).length}</span>
            <span className="text-[10px] text-slate-400">Total Plants</span>
          </div>
          <span className="text-[9px] text-slate-500 mt-2 block truncate">
            {scaleCounts.flower || 0} Flowers • {scaleCounts.bush || 0} Bushes
          </span>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/60 rounded-xl p-2.5 flex flex-col justify-between">
          <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Scale Health</span>
          <div className="flex items-baseline space-x-1 mt-1">
            <span className="text-xl font-black text-indigo-400">
              {Object.values(nodesMap).filter(n => n.status === 'completed').length}
            </span>
            <span className="text-[10px] text-slate-400">Completed</span>
          </div>
          <div className="w-full bg-slate-950 h-1 mt-2 rounded-full overflow-hidden flex">
            <div className="bg-emerald-500 h-full" style={{ width: `${(Object.values(nodesMap).filter(n => n.status === 'completed').length / (Object.keys(nodesMap).length || 1)) * 100}%` }} />
            <div className="bg-amber-500 h-full" style={{ width: `${(Object.values(nodesMap).filter(n => n.status === 'in_progress').length / (Object.keys(nodesMap).length || 1)) * 100}%` }} />
          </div>
        </div>
      </div>

      {/* Main Drawer Body: Left = Tree Node Navigator, Right = Floating/Dynamic Genetic Inspector */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        
        {/* ADD NODE PANEL (COLLAPSIBLE FORM) */}
        {isAddingNode && (
          <form onSubmit={handleCreateNode} className="p-3 bg-slate-900/80 border border-indigo-500/30 rounded-xl space-y-3 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex justify-between items-center border-b border-slate-800/60 pb-1.5">
              <span className="text-xs font-bold text-indigo-300">🌸 Plant New Flower (Node)</span>
              <button type="button" onClick={() => setIsAddingNode(false)} className="text-[10px] text-slate-400 hover:text-slate-200">✕</button>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="flex flex-col space-y-1">
                <label className="text-[10px] font-semibold text-slate-400 uppercase">Scale</label>
                <select 
                  value={newScale} 
                  onChange={(e: any) => setNewScale(e.target.value)} 
                  className="bg-slate-950 border border-slate-850 rounded px-2 py-1 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
                >
                  <option value="flower">🌸 Flower (Leaf Task)</option>
                  <option value="bush">🌿 Bush (Task Group)</option>
                </select>
              </div>

              <div className="flex flex-col space-y-1">
                <label className="text-[10px] font-semibold text-slate-400 uppercase">Parent Bush/Tree</label>
                <select 
                  value={newParentId} 
                  onChange={(e: any) => setNewParentId(e.target.value)} 
                  className="bg-slate-950 border border-slate-850 rounded px-2 py-1 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
                >
                  {Object.values(nodesMap)
                    .filter(n => n.plant_scale === 'bush' || n.plant_scale === 'tree')
                    .map(parent => (
                      <option key={parent.id} value={parent.id}>
                        {getScaleIcon(parent.plant_scale)} {parent.title}
                      </option>
                    ))
                  }
                </select>
              </div>
            </div>

            <div className="flex flex-col space-y-1">
              <label className="text-[10px] font-semibold text-slate-400 uppercase">Flower (Task) Title</label>
              <input 
                type="text"
                placeholder="Enter task name..."
                value={newTitle}
                onChange={e => setNewTitle(e.target.value)}
                className="bg-slate-950 border border-slate-850 rounded px-2 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 w-full"
              />
            </div>

            <div className="flex flex-col space-y-1">
              <label className="text-[10px] font-semibold text-slate-400 uppercase">Assigned Agent</label>
              <select 
                value={newAgent} 
                onChange={e => setNewAgent(e.target.value)} 
                className="bg-slate-950 border border-slate-850 rounded px-2 py-1 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
              >
                <option value="gerych_builder">🤖 gerych_builder</option>
                <option value="gerych_auditor">🛡️ gerych_auditor</option>
                <option value="dnk_shopify">🛍️ dnk_shopify</option>
                <option value="dnk_dev_fullstack">⚡ dnk_dev_fullstack</option>
                <option value="dnk_video_ai_creator">🎬 dnk_video_ai_creator</option>
              </select>
            </div>

            <button 
              type="submit" 
              className="w-full py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded font-bold text-xs border border-indigo-500/40 transition-colors"
            >
              Add Node to Canvas Forest
            </button>
          </form>
        )}

        {/* LOADING INDICATOR */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-16 space-y-3">
            <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-xs font-semibold text-slate-400 font-mono">Parsing 5-Plant Taxonomy graph...</span>
          </div>
        ) : (
          <div className="space-y-1">
            {rootField && renderTreeNode(rootField)}
          </div>
        )}

        {/* GENETIC NODE INSPECTOR CARD */}
        {selectedNode && (
          <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-4 space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-300">
            {/* Inspector Title */}
            <div className="flex justify-between items-start border-b border-slate-800/80 pb-2">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm">{getScaleIcon(selectedNode.plant_scale)}</span>
                  <span className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded border ${getStatusColor(selectedNode.status)}`}>
                    {selectedNode.plant_scale} • {selectedNode.status}
                  </span>
                </div>
                <h3 className="text-sm font-bold text-white mt-1.5">{selectedNode.title}</h3>
              </div>
              <button 
                onClick={() => setSelectedNode(null)} 
                className="text-[10px] text-slate-400 hover:text-slate-200 p-0.5"
              >
                ✕ Close
              </button>
            </div>

            {/* Details Fields */}
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="bg-slate-950/60 border border-slate-850/60 rounded-lg p-2 flex flex-col justify-center">
                <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Assigned Agent</span>
                <span className="font-mono text-slate-200 mt-1 flex items-center space-x-1.5">
                  <span>🤖</span> <span>{selectedNode.assigned_agent || 'unassigned'}</span>
                </span>
              </div>
              
              <div className="bg-slate-950/60 border border-slate-850/60 rounded-lg p-2 flex flex-col justify-center">
                <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Author / Creator</span>
                <span className="font-semibold text-slate-200 mt-1 flex items-center space-x-1.5">
                  <span>👑</span> <span>{selectedNode.author || 'Maksym'}</span>
                </span>
              </div>

              <div className="bg-slate-950/60 border border-slate-850/60 rounded-lg p-2 flex flex-col justify-center">
                <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Verification Status</span>
                <span className={`font-semibold mt-1 flex items-center space-x-1.5 ${
                  selectedNode.verification_status === 'verified' ? 'text-emerald-400' : 'text-slate-400'
                }`}>
                  <span>{selectedNode.verification_status === 'verified' ? '🟢' : '⚪'}</span> 
                  <span>{selectedNode.verification_status || 'pending'}</span>
                </span>
              </div>

              <div className="bg-slate-950/60 border border-slate-850/60 rounded-lg p-2 flex flex-col justify-center">
                <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Weight & Impact</span>
                <span className="font-bold text-slate-300 mt-1">{selectedNode.weight}x multiplier</span>
              </div>
            </div>

            {/* Mutation Controls for Flowers */}
            {(selectedNode.plant_scale === 'flower' || selectedNode.plant_scale === 'bush') && (
              <div className="bg-slate-950/60 border border-slate-850/60 rounded-xl p-3 space-y-2">
                <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">Mutate Plant Status</span>
                <div className="flex gap-1.5">
                  {(['todo', 'in_progress', 'completed'] as const).map(st => (
                    <button
                      key={st}
                      type="button"
                      onClick={() => handleMutateNode(selectedNode.id, st, st === 'completed' ? 100 : st === 'in_progress' ? 50 : 0)}
                      className={`flex-1 py-1 rounded text-xs font-bold capitalize border transition-all ${
                        selectedNode.status === st 
                          ? 'bg-indigo-600 border-indigo-500 text-white shadow' 
                          : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {st.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* DTO Contract Spec Box */}
            {selectedNode.dto_contract && (
              <div className="space-y-1.5">
                <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">🧬 DTO Contract JSON Spec</span>
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-850 overflow-x-auto max-h-[140px] font-mono text-[10px] text-indigo-300">
                  <pre>{JSON.stringify(selectedNode.dto_contract, null, 2)}</pre>
                </div>
              </div>
            )}

            {/* Git Diff Code Box */}
            {selectedNode.git_diff && (
              <div className="space-y-1.5">
                <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">⚙️ Commit Git Diff Trace</span>
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-850 overflow-x-auto max-h-[180px] font-mono text-[10px] text-slate-300 leading-relaxed">
                  <pre className="whitespace-pre-wrap">{selectedNode.git_diff}</pre>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer & Timeline Scrubber */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-900/40 space-y-3 shrink-0">
        <div className="flex justify-between items-center">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1">
            <span>⏱️</span> <span>Time-Travel Scrubber</span>
          </span>
          <span className="text-[10px] font-mono text-slate-400 bg-slate-950 border border-slate-850 px-1.5 py-0.5 rounded">
            {historySliderVal === historyEvents.length ? 'Live Feed' : `Step ${historySliderVal}/${historyEvents.length}`}
          </span>
        </div>

        {historyEvents.length > 0 ? (
          <div className="space-y-1.5">
            <input 
              type="range" 
              min={1} 
              max={historyEvents.length} 
              value={historySliderVal}
              onChange={e => handleScrubberChange(Number(e.target.value))}
              className="w-full accent-indigo-500 h-1.5 bg-slate-950 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-[9px] font-mono text-slate-500">
              <span>Seed Creation</span>
              <span>{historySliderVal === historyEvents.length ? 'Real-Time Present 🟢' : 'Historical Snapshot'}</span>
            </div>
          </div>
        ) : (
          <div className="text-center py-2">
            <span className="text-[10px] font-mono text-slate-500">No evolutionary mutations recorded yet.</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default StitchTaskForestDrawer;
