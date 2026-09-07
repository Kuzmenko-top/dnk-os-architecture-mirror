// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_cabinet_PRInspectorTab"
// purpose: "Working Cabinet PR Inspector & CI/CD Checks UI Component with DNK-UX-003 Diff Tree & AST changes"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  GitPullRequest,
  CheckCircle2,
  Clock,
  XCircle,
  AlertCircle,
  FileText,
  RefreshCw,
  GitBranch,
  ShieldCheck,
  ChevronRight,
  Database,
  Code2,
  FolderTree
} from "lucide-react";
import {
  cabinetApi,
  GitHubPRListItem,
  GitHubCheckRun,
  GitHubChangedFile,
  PRDiffResponse,
  PRASTDiffResponse,
  ParsedFileDiff,
  ASTFileDiff
} from "@/lib/api_client";
import { FileDiffTree } from "./FileDiffTree";
import { DiffViewer } from "./DiffViewer";
import { ASTChangesBadge } from "./ASTChangesBadge";

export function PRInspectorTab() {
  const [prs, setPrs] = useState<GitHubPRListItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedPrNumber, setSelectedPrNumber] = useState<number | null>(30);
  const [prChecks, setPrChecks] = useState<GitHubCheckRun[]>([]);
  const [prFiles, setPrFiles] = useState<GitHubChangedFile[]>([]);
  const [loadingDetails, setLoadingDetails] = useState<boolean>(false);

  // DNK-UX-003 State
  const [inspectorSubTab, setInspectorSubTab] = useState<"checks" | "files">("files");
  const [prDiff, setPrDiff] = useState<PRDiffResponse | null>(null);
  const [prAstDiff, setPrAstDiff] = useState<PRASTDiffResponse | null>(null);
  const [selectedFilePath, setSelectedFilePath] = useState<string>("");
  const [diffViewMode, setDiffViewMode] = useState<"unified" | "split">("unified");
  const [treeSearchQuery, setTreeSearchQuery] = useState<string>("");
  const [loadingFileDiff, setLoadingFileDiff] = useState<boolean>(false);

  const [envelopeMeta, setEnvelopeMeta] = useState<{
    data_source: string;
    stale: boolean;
    fetched_at?: string;
  }>({ data_source: "live", stale: false });

  const owner = "Kuzmenko-top";
  const repo = "DNK_OS_MVP";

  const fetchPRs = async () => {
    setLoading(true);
    try {
      const res = await cabinetApi.getGitHubPRs(owner, repo);
      if (res && res.data) {
        setPrs(res.data);
        setEnvelopeMeta({
          data_source: res.data_source,
          stale: res.stale,
          fetched_at: res.fetched_at
        });
      }
    } catch (e) {
      console.error("Failed to load PRs", e);
    } finally {
      setLoading(false);
    }
  };

  const fetchPRDetails = async (prNumber: number) => {
    setSelectedPrNumber(prNumber);
    setLoadingDetails(true);
    try {
      const selectedPr = prs.find((p) => p.number === prNumber);
      const ref = selectedPr?.head_sha;

      const [checksRes, filesRes, diffRes, astRes] = await Promise.all([
        cabinetApi.getGitHubPRChecks(owner, repo, prNumber, ref),
        cabinetApi.getGitHubPRFiles(owner, repo, prNumber),
        cabinetApi.getGitHubPRDiff(owner, repo, prNumber),
        cabinetApi.getGitHubPRASTDiff(owner, repo, prNumber)
      ]);

      if (checksRes && checksRes.data && checksRes.data.check_runs) {
        setPrChecks(checksRes.data.check_runs);
      } else {
        setPrChecks([]);
      }

      if (filesRes && filesRes.data && filesRes.data.files) {
        setPrFiles(filesRes.data.files);
      } else {
        setPrFiles([]);
      }

      if (diffRes && diffRes.data) {
        setPrDiff(diffRes.data);
        if (diffRes.data.files && diffRes.data.files.length > 0) {
          setSelectedFilePath(diffRes.data.files[0].filename);
        }
      } else {
        setPrDiff(null);
      }

      if (astRes && astRes.data) {
        setPrAstDiff(astRes.data);
      } else {
        setPrAstDiff(null);
      }
    } catch (e) {
      console.error("Failed to load PR details", e);
    } finally {
      setLoadingDetails(false);
    }
  };

  useEffect(() => {
    fetchPRs();
  }, []);

  useEffect(() => {
    if (selectedPrNumber) {
      fetchPRDetails(selectedPrNumber);
    }
  }, [selectedPrNumber]);

  const selectedPr = prs.find((p) => p.number === selectedPrNumber) || prs[0];

  const currentSelectedFileDiff = useMemo<ParsedFileDiff | undefined>(() => {
    if (!prDiff || !prDiff.files) return undefined;
    return prDiff.files.find((f) => f.filename === selectedFilePath);
  }, [prDiff, selectedFilePath]);

  const currentSelectedAstDiff = useMemo<ASTFileDiff | undefined>(() => {
    if (!prAstDiff || !prAstDiff.ast_diffs) return undefined;
    return prAstDiff.ast_diffs.find((a) => a.filename === selectedFilePath);
  }, [prAstDiff, selectedFilePath]);

  return (
    <div className="space-y-6">
      {/* Header & Meta Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-blue-500/10 text-blue-400 rounded-lg border border-blue-500/20">
            <GitPullRequest className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
              PR Inspector & Diff Engine
              <span className="text-xs px-2 py-0.5 rounded font-mono bg-cyan-950 text-cyan-400 border border-cyan-800/40">
                DNK-UX-003
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              {owner}/{repo} • Tree Diff, AST Change Extraction & CI Checks
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 text-xs font-mono px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg">
            <Database className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-slate-400">Source:</span>
            <span className="text-slate-200 uppercase font-semibold">
              {envelopeMeta.data_source}
            </span>
            {envelopeMeta.stale && (
              <span className="text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded">
                stale
              </span>
            )}
          </div>

          <button
            onClick={() => {
              fetchPRs();
              if (selectedPrNumber) fetchPRDetails(selectedPrNumber);
            }}
            className="p-2 text-slate-400 hover:text-slate-200 bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 transition-colors"
            title="Refresh PR Data"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Main Grid: PR List Sidebar + Inspector Details */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Col: PR List (4 cols) */}
        <div className="lg:col-span-4 bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col h-[750px]">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center justify-between">
            <span>Pull Requests ({prs.length})</span>
            <GitBranch className="w-3.5 h-3.5 text-slate-500" />
          </h3>

          <div className="flex-1 overflow-y-auto space-y-2 pr-1">
            {prs.map((pr) => {
              const isSelected = pr.number === selectedPrNumber;
              return (
                <div
                  key={pr.number}
                  onClick={() => setSelectedPrNumber(pr.number)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    isSelected
                      ? "bg-blue-950/40 border-blue-500/50 shadow-md"
                      : "bg-slate-950/40 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/60"
                  }`}
                >
                  <div className="flex items-center justify-between text-xs font-mono mb-1">
                    <span className="font-bold text-blue-400">#{pr.number}</span>
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${
                        pr.state.toUpperCase() === "OPEN"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                      }`}
                    >
                      {pr.state}
                    </span>
                  </div>

                  <h4 className="text-xs font-medium text-slate-200 line-clamp-2 mb-2">
                    {pr.title}
                  </h4>

                  <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
                    <span className="truncate max-w-[120px]">by @{pr.user_login}</span>
                    <div className="flex items-center space-x-1.5">
                      <span className="text-emerald-400">+{pr.additions}</span>
                      <span className="text-rose-400">-{pr.deletions}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Col: Inspector Workspace (8 cols) */}
        <div className="lg:col-span-8 bg-slate-900/60 border border-slate-800 rounded-xl p-5 flex flex-col h-[750px]">
          {selectedPr ? (
            <div className="flex flex-col h-full space-y-4">
              {/* Selected PR Sub-Header */}
              <div className="pb-3 border-b border-slate-800 flex items-start justify-between">
                <div>
                  <div className="flex items-center space-x-2 text-xs font-mono text-slate-400 mb-1">
                    <span className="text-blue-400 font-bold">#{selectedPr.number}</span>
                    <span>•</span>
                    <span className="text-slate-300">{selectedPr.head_branch}</span>
                    <span>→</span>
                    <span className="text-slate-300">{selectedPr.base_branch}</span>
                  </div>
                  <h3 className="text-base font-semibold text-slate-100">
                    {selectedPr.title}
                  </h3>
                </div>

                {/* Sub-Tab Controls */}
                <div className="flex p-1 bg-slate-950 border border-slate-800 rounded-lg text-xs font-medium">
                  <button
                    onClick={() => setInspectorSubTab("files")}
                    className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-colors ${
                      inspectorSubTab === "files"
                        ? "bg-slate-800 text-cyan-300 font-semibold"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    <FolderTree className="w-3.5 h-3.5" />
                    Files Changed ({prDiff?.total_files || prFiles.length})
                  </button>
                  <button
                    onClick={() => setInspectorSubTab("checks")}
                    className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-colors ${
                      inspectorSubTab === "checks"
                        ? "bg-slate-800 text-cyan-300 font-semibold"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    <ShieldCheck className="w-3.5 h-3.5" />
                    CI Checks ({prChecks.length})
                  </button>
                </div>
              </div>

              {/* Inspector Content Area */}
              <div className="flex-1 overflow-hidden">
                {inspectorSubTab === "checks" ? (
                  /* Checks Tab Content */
                  <div className="h-full overflow-y-auto space-y-2 pr-1">
                    {prChecks.length === 0 ? (
                      <div className="p-8 text-center text-slate-500 text-xs font-mono">
                        No CI checks recorded for this commit/pull request.
                      </div>
                    ) : (
                      prChecks.map((check) => (
                        <div
                          key={check.id}
                          className="flex items-center justify-between p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg text-xs"
                        >
                          <div className="flex items-center space-x-2.5">
                            {check.conclusion === "success" ? (
                              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                            ) : check.status === "in_progress" ? (
                              <Clock className="w-4 h-4 text-amber-400 animate-pulse" />
                            ) : (
                              <XCircle className="w-4 h-4 text-rose-400" />
                            )}
                            <div>
                              <span className="font-semibold text-slate-200">{check.name}</span>
                              <p className="text-[10px] text-slate-500 font-mono">
                                App: {check.app_name}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center space-x-2 text-[10px] font-mono">
                            <span
                              className={`px-1.5 py-0.5 rounded uppercase ${
                                check.conclusion === "success"
                                  ? "bg-emerald-500/10 text-emerald-400"
                                  : "bg-rose-500/10 text-rose-400"
                              }`}
                            >
                              {check.conclusion || check.status}
                            </span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                ) : (
                  /* Files Changed / Diff Tab Content (DNK-UX-003) */
                  <div className="flex flex-col h-full space-y-3">
                    {/* Top AST Summary Bar if selected file has AST changes */}
                    <div className="flex items-center justify-between bg-slate-950/60 p-2 border border-slate-800 rounded-lg text-xs">
                      <div className="flex items-center gap-2 truncate">
                        <span className="text-slate-400 font-mono">File:</span>
                        <span className="font-semibold text-slate-200 truncate">
                          {selectedFilePath || "Select a file"}
                        </span>
                      </div>

                      <div className="flex items-center gap-2">
                        {currentSelectedAstDiff && (
                          <ASTChangesBadge astDiff={currentSelectedAstDiff} />
                        )}
                      </div>
                    </div>

                    {/* Split View: Left Tree + Right Diff Viewer */}
                    <div className="grid grid-cols-12 gap-3 flex-1 overflow-hidden">
                      {/* Left: Tree View (4 cols) */}
                      <div className="col-span-4 h-full">
                        <FileDiffTree
                          treeNode={prDiff?.tree}
                          selectedPath={selectedFilePath}
                          onSelectFile={(path) => setSelectedFilePath(path)}
                          searchQuery={treeSearchQuery}
                          onSearchChange={(q) => setTreeSearchQuery(q)}
                        />
                      </div>

                      {/* Right: Diff Viewer (8 cols) */}
                      <div className="col-span-8 h-full">
                        <DiffViewer
                          fileDiff={currentSelectedFileDiff}
                          viewMode={diffViewMode}
                          onViewModeChange={(m) => setDiffViewMode(m)}
                          isLoading={loadingFileDiff}
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-slate-500 text-xs font-mono">
              Select a pull request to inspect details.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
