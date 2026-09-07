// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_MindMapEvidenceNode"
// purpose: "Mind Map Resource & Evidence Node (Purple folder card) for linking source files, documentation, and external research"
// author: "DNK-e.com Maksym & Antigravity Mentor"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-04"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { NodeProps } from '@xyflow/react';
import { FolderGit2, ExternalLink, FileCode, Globe, FileText, Check, Edit2 } from 'lucide-react';
import BaseMindMapNode from './BaseMindMapNode';
import { useCanvasStore } from '../../../store/canvasStore';

export type EvidenceType = 'file' | 'link' | 'code' | 'doc';

export interface MindMapEvidenceData {
  title?: string;
  description?: string;
  evidence_type?: EvidenceType;
  target_uri?: string;
  preview?: string;
  [key: string]: any;
}

const TYPE_ICONS: Record<EvidenceType, React.ReactNode> = {
  file: <FileText className="w-3.5 h-3.5 text-purple-400" />,
  link: <Globe className="w-3.5 h-3.5 text-purple-400" />,
  code: <FileCode className="w-3.5 h-3.5 text-purple-400" />,
  doc: <FolderGit2 className="w-3.5 h-3.5 text-purple-400" />,
};

export default function MindMapEvidenceNode(props: NodeProps) {
  const { id, data } = props;
  const nodeData = (data || {}) as MindMapEvidenceData;
  const updateNodeData = useCanvasStore((state) => state.updateNodeData);

  const evidenceType = nodeData.evidence_type || 'file';
  const targetUri = nodeData.target_uri || 'docs/architecture/UNIFIED_SPATIAL_CANVAS_SYSTEM_SYNTHESIS.md';

  const [isEditingUri, setIsEditingUri] = useState(false);
  const [uriText, setUriText] = useState(targetUri);

  const handleSaveUri = () => {
    setIsEditingUri(false);
    if (uriText.trim() !== targetUri) {
      updateNodeData(id, { target_uri: uriText.trim() });
    }
  };

  const handleOpenLink = () => {
    if (targetUri.startsWith('http://') || targetUri.startsWith('https://')) {
      window.open(targetUri, '_blank', 'noopener,noreferrer');
    } else {
      // In web app, emit console or handle relative path preview
      console.log('Opening local evidence artifact:', targetUri);
    }
  };

  return (
    <BaseMindMapNode
      {...props}
      themeColor="purple"
      icon={<FolderGit2 className="w-4 h-4" />}
      categoryLabel="Resource"
    >
      <div className="flex flex-col gap-2">
        {/* Type Icon + Editable Target Path */}
        <div className="flex items-center justify-between gap-1 text-[11px] bg-slate-900/80 border border-purple-500/20 rounded-md p-1.5">
          <div className="flex items-center gap-1.5 min-w-0 flex-1">
            {TYPE_ICONS[evidenceType]}
            {isEditingUri ? (
              <div className="flex items-center gap-1 flex-1">
                <input
                  type="text"
                  value={uriText}
                  onChange={(e) => setUriText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSaveUri();
                    if (e.key === 'Escape') setIsEditingUri(false);
                  }}
                  autoFocus
                  className="w-full bg-[#161c28] border border-purple-500/40 rounded px-1 text-[10px] text-purple-200 font-mono focus:outline-none"
                />
                <button
                  onClick={handleSaveUri}
                  className="text-emerald-400 hover:text-emerald-300 p-0.5"
                >
                  <Check className="w-3 h-3" />
                </button>
              </div>
            ) : (
              <span
                onDoubleClick={() => setIsEditingUri(true)}
                className="font-mono text-[10px] text-purple-300 truncate cursor-pointer hover:underline"
                title={targetUri}
              >
                {targetUri.split('/').pop() || targetUri}
              </span>
            )}
          </div>

          <button
            onClick={handleOpenLink}
            className="p-1 rounded text-slate-400 hover:text-purple-300 hover:bg-purple-950/40 transition-colors"
            title="Open Resource"
          >
            <ExternalLink className="w-3 h-3" />
          </button>
        </div>

        {/* Preview Snippet */}
        {nodeData.preview && (
          <div className="p-1.5 rounded bg-[#090b10] border border-slate-800 text-[10px] text-slate-400 font-mono line-clamp-2">
            {nodeData.preview}
          </div>
        )}
      </div>
    </BaseMindMapNode>
  );
}
