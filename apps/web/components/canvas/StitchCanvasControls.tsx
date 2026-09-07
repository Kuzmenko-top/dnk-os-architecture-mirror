// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_StitchCanvasControls"
// purpose: "Google Stitch Bottom-Right Zoom and History Controls"
// author: "DNK-e.com Maksym"
// status: "Active"
// version: "3.1.0"
// updated_at: "2026-09-03"
// --- END DNK-MRH-HEADER ---

'use client';

import React from 'react';
import { Undo2, Redo2, HelpCircle } from 'lucide-react';
import { useReactFlow } from '@xyflow/react';

export default function StitchCanvasControls() {
  let zoomIn = () => {};
  let zoomOut = () => {};
  let fitView = () => {};
  
  try {
    const reactFlowInstance = useReactFlow();
    zoomIn = reactFlowInstance.zoomIn;
    zoomOut = reactFlowInstance.zoomOut;
    fitView = reactFlowInstance.fitView;
  } catch (e) {
    // Context safety block
  }

  return (
    <div className="absolute bottom-6 right-6 z-30 flex items-center gap-3">
      {/* Undo/Redo & Zoom Group */}
      <div className="flex items-center gap-2.5 bg-[#16181f]/95 border border-white/10 rounded-full px-3 py-1.5 shadow-2xl backdrop-blur-2xl">
        <button
          onClick={() => console.log('Undo canvas action')}
          className="p-1 text-neutral-400 hover:text-white hover:bg-white/5 rounded-full transition-colors"
          title="Undo (Cmd+Z)"
        >
          <Undo2 className="w-4 h-4" />
        </button>
        
        <button
          onClick={() => console.log('Redo canvas action')}
          className="p-1 text-neutral-400 hover:text-white hover:bg-white/5 rounded-full transition-colors"
          title="Redo (Shift+Cmd+Z)"
        >
          <Redo2 className="w-4 h-4" />
        </button>

        <div className="h-4 w-px bg-white/10" />

        {/* Zoom Selector Display */}
        <button
          onClick={() => fitView()}
          className="text-[11px] font-semibold text-neutral-300 hover:text-white px-2 py-0.5 rounded transition-colors"
          title="Fit to Screen"
        >
          23%
        </button>
      </div>

      {/* Help Circle Button */}
      <button
        onClick={() => alert('Welcome to Google Stitch on DNK OS Canvas! Use spacebar + drag to pan, scroll wheel to zoom.')}
        className="flex items-center justify-center p-2 bg-[#16181f]/95 border border-white/10 text-neutral-400 hover:text-white hover:bg-white/5 rounded-full shadow-2xl backdrop-blur-2xl transition-colors"
        title="Help & Shortcuts"
      >
        <HelpCircle className="w-4 h-4" />
      </button>
    </div>
  );
}
