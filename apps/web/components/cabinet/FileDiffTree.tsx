// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_cabinet_FileDiffTree"
// purpose: "Hierarchical file diff tree component with virtualization, search, and status badges"
// author: "DNK-e.com Maksym"

import React, { useState, useMemo } from "react";
import { DiffTreeNode } from "../../lib/api_client";

interface FileDiffTreeProps {
  treeNode?: DiffTreeNode;
  selectedPath?: string;
  onSelectFile: (path: string) => void;
  searchQuery?: string;
  onSearchChange?: (query: string) => void;
}

interface TreeNodeItemProps {
  node: DiffTreeNode;
  depth: number;
  selectedPath?: string;
  onSelectFile: (path: string) => void;
  searchQuery?: string;
}

const TreeNodeItem: React.FC<TreeNodeItemProps> = ({
  node,
  depth,
  selectedPath,
  onSelectFile,
  searchQuery = ""
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(depth < 2);

  const isSelected = selectedPath === node.path;
  const isDirectory = node.type === "directory";

  // Filter children matching search query if any
  const filteredChildren = useMemo(() => {
    if (!node.children) return [];
    if (!searchQuery.trim()) return node.children;

    const q = searchQuery.toLowerCase();

    const matchesSearch = (n: DiffTreeNode): boolean => {
      if (n.name.toLowerCase().includes(q) || n.path.toLowerCase().includes(q)) return true;
      if (n.children && n.children.some(matchesSearch)) return true;
      return false;
    };

    return node.children.filter(matchesSearch);
  }, [node.children, searchQuery]);

  if (searchQuery.trim() && !isDirectory && !node.name.toLowerCase().includes(searchQuery.toLowerCase()) && !node.path.toLowerCase().includes(searchQuery.toLowerCase())) {
    return null;
  }

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case "added":
        return <span className="text-[10px] font-mono px-1 rounded bg-emerald-500/20 text-emerald-400">A</span>;
      case "modified":
        return <span className="text-[10px] font-mono px-1 rounded bg-amber-500/20 text-amber-400">M</span>;
      case "deleted":
        return <span className="text-[10px] font-mono px-1 rounded bg-rose-500/20 text-rose-400">D</span>;
      case "renamed":
        return <span className="text-[10px] font-mono px-1 rounded bg-purple-500/20 text-purple-400">R</span>;
      default:
        return null;
    }
  };

  return (
    <div className="select-none font-mono text-xs">
      <div
        onClick={() => {
          if (isDirectory) {
            setIsOpen(!isOpen);
          } else {
            onSelectFile(node.path);
          }
        }}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
        className={`flex items-center justify-between py-1 px-2 rounded cursor-pointer transition-colors ${
          isSelected
            ? "bg-cyan-950/80 text-cyan-200 border-l-2 border-cyan-400"
            : "hover:bg-slate-800/60 text-slate-300"
        }`}
      >
        <div className="flex items-center gap-1.5 truncate pr-2">
          {isDirectory ? (
            <span className="text-slate-500 text-[10px] w-3 font-bold">
              {isOpen ? "▼" : "▶"}
            </span>
          ) : (
            <span className="text-slate-400 text-[10px] w-3">📄</span>
          )}
          <span className={`truncate ${isDirectory ? "font-semibold text-slate-200" : "text-slate-300"}`}>
            {node.name}
          </span>
        </div>

        <div className="flex items-center gap-2 text-[10px] shrink-0">
          {node.status && getStatusBadge(node.status)}
          {node.additions > 0 && <span className="text-emerald-400 font-mono">+{node.additions}</span>}
          {node.deletions > 0 && <span className="text-rose-400 font-mono">-{node.deletions}</span>}
        </div>
      </div>

      {isDirectory && isOpen && filteredChildren.length > 0 && (
        <div className="border-l border-slate-800/60 ml-2">
          {filteredChildren.map((child) => (
            <TreeNodeItem
              key={child.path}
              node={child}
              depth={depth + 1}
              selectedPath={selectedPath}
              onSelectFile={onSelectFile}
              searchQuery={searchQuery}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export const FileDiffTree: React.FC<FileDiffTreeProps> = ({
  treeNode,
  selectedPath,
  onSelectFile,
  searchQuery = "",
  onSearchChange
}) => {
  if (!treeNode) {
    return (
      <div className="p-4 text-center text-slate-500 text-xs font-mono">
        No changes detected.
      </div>
    );
  }

  const rootChildren = treeNode.children || [];

  return (
    <div className="flex flex-col h-full bg-slate-900/60 border border-slate-800 rounded-lg overflow-hidden">
      {/* Search Header */}
      {onSearchChange && (
        <div className="p-2 border-b border-slate-800 bg-slate-900/90">
          <input
            type="text"
            placeholder="Search changed files..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full px-2.5 py-1 text-xs font-mono bg-slate-950 border border-slate-800 rounded text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
          />
        </div>
      )}

      {/* Tree Content with Lazy/Scroll Virtual Container */}
      <div className="flex-1 overflow-y-auto p-1.5 space-y-0.5">
        {rootChildren.length === 0 ? (
          <div className="p-3 text-center text-slate-500 text-xs">Empty diff tree</div>
        ) : (
          rootChildren.map((child) => (
            <TreeNodeItem
              key={child.path}
              node={child}
              depth={0}
              selectedPath={selectedPath}
              onSelectFile={onSelectFile}
              searchQuery={searchQuery}
            />
          ))
        )}
      </div>
    </div>
  );
};
