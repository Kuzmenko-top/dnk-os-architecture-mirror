// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_VideoStoryboardNoteNode"
// purpose: "9:16 Kinetic UGC Video Storyboard Living Document Node for DNK OS Note-Based Canvas (Task 3) supporting scene-by-scene script editing, audio prompts, aspect ratio selector, and Remotion video rendering engine dispatch connected to useCanvasStore SSOT"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-09-03"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { 
  Film, 
  Sparkles, 
  Play, 
  CheckCircle2, 
  RefreshCw, 
  Sliders, 
  Layers, 
  ChevronDown, 
  ChevronUp,
  Clapperboard,
  Video,
  Music,
  Plus,
  Trash2,
  Tv,
  Pause,
  SlidersHorizontal
} from 'lucide-react';
import { useCanvasStore } from '../../../store/canvasStore';

export interface SceneItem {
  id: string;
  timeRange: string;
  visualPrompt: string;
  voiceover: string;
}

export interface VideoStoryboardNoteData {
  title?: string;
  aspectRatio?: '9:16' | '16:9' | '1:1';
  motionStyle?: string;
  duration?: number;
  scenes?: SceneItem[];
  renderStatus?: 'idle' | 'rendering' | 'ready';
  renderProgress?: number;
}

export default function VideoStoryboardNoteNode({ id, data, selected }: NodeProps) {
  const nodeData = (data || {}) as VideoStoryboardNoteData;
  const updateNodeData = useCanvasStore((state) => state.updateNodeData);

  const title = nodeData.title || 'ReBurn 9:16 Kinetic Product Reveal';
  const aspectRatio = nodeData.aspectRatio || '9:16';
  const motionStyle = nodeData.motionStyle || 'Cyberpunk Neon Motion';
  const duration = nodeData.duration || 15;
  const renderStatus = nodeData.renderStatus || 'idle';
  const renderProgress = nodeData.renderProgress || 0;
  
  const [isExpanded, setIsExpanded] = useState<boolean>(true);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackTime, setPlaybackTime] = useState<number>(0);

  const scenes = Array.isArray(nodeData.scenes) && nodeData.scenes.length > 0
    ? nodeData.scenes
    : [
        { id: 'sc1', timeRange: '0:00 - 0:03', visualPrompt: 'Macro shot of titanium cocktail smoker infusing applewood smoke with emerald laser glow.', voiceover: '"Tired of ordinary drinks? Meet ReBurn."' },
        { id: 'sc2', timeRange: '0:03 - 0:08', visualPrompt: 'Fast-paced kinetic camera zoom highlighting 3-in-1 cocktail bundle components and accessories.', voiceover: '"Infuse rich bar-grade smoke in under 10 seconds."' },
        { id: 'sc3', timeRange: '0:08 - 0:15', visualPrompt: 'Call to action card with glowing $45 discount badge and 1-click checkout button.', voiceover: '"Claim your 3-in-1 bundle today. Link below."' },
      ];

  const handleStartRender = () => {
    updateNodeData(id, { renderStatus: 'rendering', renderProgress: 5 });

    let progress = 5;
    const interval = setInterval(() => {
      progress += 20;
      if (progress >= 100) {
        clearInterval(interval);
        updateNodeData(id, { renderStatus: 'ready', renderProgress: 100 });
      } else {
        updateNodeData(id, { renderProgress: progress });
      }
    }, 350);
  };

  const handleTitleChange = (val: string) => {
    updateNodeData(id, { title: val });
  };

  const handleAspectRatioChange = (val: '9:16' | '16:9' | '1:1') => {
    updateNodeData(id, { aspectRatio: val });
  };

  const togglePlayback = () => {
    setIsPlaying(!isPlaying);
    if (!isPlaying) {
      const interval = setInterval(() => {
        setPlaybackTime((prev) => {
          if (prev >= duration) {
            clearInterval(interval);
            setIsPlaying(false);
            return 0;
          }
          return prev + 1;
        });
      }, 1000);
    }
  };

  return (
    <div className={`w-[460px] rounded-3xl bg-[#02090a]/95 backdrop-blur-2xl border border-[#1e2c31] p-5 text-white shadow-[0_16px_50px_rgba(0,0,0,0.9)] transition-all duration-200 ${
      selected ? 'border-[#36f4a4] ring-1 ring-[#36f4a4] shadow-[0_0_35px_rgba(54,244,164,0.25)]' : ''
    }`}>
      {/* 4-Way Semantic Handles */}
      <Handle type="target" position={Position.Top} className="w-2.5 h-2.5 bg-[#36f4a4] border-2 border-[#02090a] rounded-full" />
      <Handle type="source" position={Position.Bottom} className="w-2.5 h-2.5 bg-[#36f4a4] border-2 border-[#02090a] rounded-full" />
      <Handle type="target" position={Position.Left} id="left" className="w-2.5 h-2.5 bg-[#36f4a4] border-2 border-[#02090a] rounded-full" />
      <Handle type="source" position={Position.Right} id="right" className="w-2.5 h-2.5 bg-[#36f4a4] border-2 border-[#02090a] rounded-full" />

      {/* Header */}
      <div className="flex items-start justify-between border-b border-[#1e2c31] pb-3 mb-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-2xl bg-[#102620] border border-[#36f4a4]/40 flex items-center justify-center text-[#36f4a4] shadow-sm">
            <Film className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={title}
                onChange={(e) => handleTitleChange(e.target.value)}
                className="font-bold text-sm text-white bg-transparent border-none focus:outline-none focus:ring-1 focus:ring-[#36f4a4] rounded px-1 max-w-[200px]"
              />
              <select
                value={aspectRatio}
                onChange={(e) => handleAspectRatioChange(e.target.value as '9:16' | '16:9' | '1:1')}
                className="px-2 py-0.5 rounded-full text-[9px] font-mono bg-[#102620] text-[#36f4a4] border border-[#36f4a4]/30 font-bold focus:outline-none cursor-pointer"
              >
                <option value="9:16">9:16</option>
                <option value="16:9">16:9</option>
                <option value="1:1">1:1</option>
              </select>
            </div>
            <p className="text-[11px] text-[#a1a1aa] font-mono truncate">{motionStyle} • {duration}s</p>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 rounded-full hover:bg-[#061a1c] text-[#a1a1aa] hover:text-white transition-colors cursor-pointer"
          >
            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {isExpanded && (
        <>
          {/* Storyboard Scene Breakdown */}
          <div className="space-y-2 mb-3">
            <div className="flex items-center justify-between text-[11px] font-mono text-[#a1a1aa] px-1">
              <span>Scene-by-Scene Storyboard</span>
              <span className="text-[#36f4a4]">Remotion Engine</span>
            </div>

            <div className="space-y-1.5 max-h-[160px] overflow-y-auto pr-1">
              {scenes.map((scene) => (
                <div key={scene.id} className="p-2.5 rounded-2xl bg-[#061a1c] border border-[#1e2c31] text-xs font-mono">
                  <div className="flex items-center justify-between text-[10px] text-[#36f4a4] mb-1 font-bold">
                    <span className="flex items-center gap-1">
                      <Clapperboard className="w-3 h-3" />
                      <span>{scene.timeRange}</span>
                    </span>
                    <span className="text-[#71717a] font-normal">Remotion Layer</span>
                  </div>
                  <p className="text-[#d4d4d8] text-[11px] leading-relaxed mb-1 font-sans">{scene.visualPrompt}</p>
                  <div className="p-1.5 rounded-xl bg-[#02090a] border border-[#1e2c31] text-[10px] text-[#a1a1aa] italic flex items-center gap-1.5">
                    <Music className="w-3 h-3 text-[#36f4a4] shrink-0" />
                    <span className="truncate">{scene.voiceover}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Render Progress Bar if rendering */}
          {renderStatus === 'rendering' && (
            <div className="p-2.5 rounded-2xl bg-[#061a1c] border border-[#1e2c31] mb-3">
              <div className="flex items-center justify-between text-[10px] font-mono text-[#a1a1aa] mb-1">
                <span className="flex items-center gap-1.5 text-[#36f4a4]">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Generating Video Frames...</span>
                </span>
                <span className="text-[#36f4a4] font-bold">{renderProgress}%</span>
              </div>
              <div className="w-full bg-[#02090a] rounded-full h-1.5 overflow-hidden">
                <div className="bg-gradient-to-r from-[#22d3ee] to-[#36f4a4] h-full transition-all duration-300" style={{ width: `${renderProgress}%` }} />
              </div>
            </div>
          )}

          {/* Video Preview Canvas once ready */}
          {renderStatus === 'ready' && (
            <div className="mb-3 p-3 rounded-2xl bg-[#02090a] border border-[#36f4a4]/20 relative overflow-hidden flex flex-col gap-2">
              <div className="relative aspect-video w-full rounded-xl bg-[#061a1c] flex items-center justify-center border border-[#1e2c31] overflow-hidden group">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(54,244,164,0.1)_0%,transparent_100%)] pointer-events-none" />
                <Tv className="w-8 h-8 text-[#36f4a4]/40 group-hover:scale-110 transition-transform duration-300" />
                <span className="absolute bottom-2.5 right-2.5 px-2 py-0.5 rounded text-[9px] font-mono bg-black/80 text-[#36f4a4] border border-[#36f4a4]/30 font-bold">
                  PREVIEW READY
                </span>
                <div className="absolute top-2.5 left-2.5 text-[10px] font-mono text-[#a1a1aa] bg-black/60 px-2 py-0.5 rounded">
                  0:0{playbackTime} / 0:{duration}
                </div>
              </div>

              {/* Mini Video Controls */}
              <div className="flex items-center gap-2 justify-between">
                <button
                  onClick={togglePlayback}
                  className="p-1.5 rounded-lg bg-[#102620] border border-[#36f4a4]/30 hover:border-[#36f4a4]/60 text-[#36f4a4] cursor-pointer"
                >
                  {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 fill-current" />}
                </button>
                <div className="flex-1 bg-[#061a1c] h-1.5 rounded-full overflow-hidden relative">
                  <div 
                    className="bg-[#36f4a4] h-full transition-all duration-200" 
                    style={{ width: `${(playbackTime / duration) * 100}%` }} 
                  />
                </div>
              </div>
            </div>
          )}

          {/* Action Trigger Button */}
          <button
            onClick={handleStartRender}
            disabled={renderStatus === 'rendering'}
            className="w-full py-2.5 px-4 rounded-full bg-[#36f4a4] hover:bg-[#2de097] disabled:bg-[#061a1c] disabled:text-[#4c5c5c] text-black font-bold font-mono text-xs flex items-center justify-center gap-2 transition-all shadow-md shadow-[#36f4a4]/10 active:scale-98 cursor-pointer"
          >
            {renderStatus === 'rendering' ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : renderStatus === 'ready' ? (
              <CheckCircle2 className="w-4 h-4 text-black" />
            ) : (
              <Play className="w-4 h-4 fill-current" />
            )}
            <span>
              {renderStatus === 'rendering'
                ? 'Synthesizing Remotion Composition...'
                : renderStatus === 'ready'
                ? 'Video Reel Ready (Re-Render)'
                : 'Compile & Render 9:16 Video Reel'}
            </span>
          </button>
        </>
      )}

      {/* Footer */}
      <div className="mt-3 pt-2.5 border-t border-[#1e2c31] flex items-center justify-between text-[10px] font-mono text-[#a1a1aa]">
        <div className="flex items-center gap-1 text-[#36f4a4]">
          <Video className="w-3 h-3" />
          <span>Remotion v4.0.0</span>
        </div>
        <span className="text-[#71717a]">1080x1920 60FPS</span>
      </div>
    </div>
  );
}
