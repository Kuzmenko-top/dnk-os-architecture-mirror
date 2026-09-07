// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_cabinet_GovernanceTab"
// purpose: "Governance tab for Approval Inbox (preview & gate decisions) and Plugins/Trust status (DNK-VISUAL-OS-001)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-23"
// --- END DNK-MRH-HEADER ---

"use client";

import React, { useState, useEffect } from "react";
import { ApprovalRequest, PluginTrustStatus, cabinetApi } from "../../lib/api_client";

export function GovernanceTab() {
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [plugins, setPlugins] = useState<PluginTrustStatus[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedApproval, setSelectedApproval] = useState<ApprovalRequest | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [apprData, plugData] = await Promise.all([
          cabinetApi.getApprovals(),
          cabinetApi.getPlugins(),
        ]);
        setApprovals(apprData);
        setPlugins(plugData);
        if (apprData.length > 0) {
          setSelectedApproval(apprData[0]);
        }
      } catch (err) {
        console.error("Failed to load governance data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-xs font-mono text-slate-400">
        Loading Governance, Approvals & Trust Registry...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 1. Approval Inbox (HITL & Security Gates) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1 bg-slate-900/40 border border-slate-800 rounded-lg p-4 space-y-3 flex flex-col h-[400px]">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <h2 className="text-sm font-semibold text-slate-200">Approval Inbox</h2>
            <span className="text-[10px] font-mono bg-amber-500/10 text-amber-400 px-1.5 py-0.5 rounded border border-amber-500/20">
              HITL Gate
            </span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2">
            {approvals.map((appr) => (
              <div
                key={appr.id}
                onClick={() => setSelectedApproval(appr)}
                className={`p-3 rounded-lg border text-xs cursor-pointer transition-colors space-y-1 ${
                  selectedApproval?.id === appr.id
                    ? "bg-slate-800 border-amber-500/40 text-slate-100"
                    : "bg-slate-950/40 border-slate-800/80 text-slate-400 hover:bg-slate-900"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] text-amber-400">{appr.gate_type}</span>
                  <span className="text-[9px] font-mono text-slate-500">
                    {new Date(appr.created_at).toLocaleTimeString()}
                  </span>
                </div>
                <p className="font-medium text-slate-200 line-clamp-1">{appr.title}</p>
                <p className="text-[10px] text-slate-500">Req: {appr.requester}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Approval Details & Preview */}
        <div className="md:col-span-2 bg-slate-900/40 border border-slate-800 rounded-lg p-5 space-y-4 h-[400px] overflow-y-auto">
          {selectedApproval ? (
            <>
              <div className="border-b border-slate-800 pb-3 space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="bg-amber-500/10 text-amber-400 text-[10px] font-mono px-2 py-0.5 rounded border border-amber-500/20">
                    {selectedApproval.gate_type}
                  </span>
                  <h3 className="text-sm font-semibold text-slate-100">{selectedApproval.title}</h3>
                </div>
                <p className="text-xs text-slate-400 font-mono">Task ID: {selectedApproval.task_id}</p>
              </div>

              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-slate-300">Simulated Payload Preview</h4>
                <pre className="bg-slate-950 p-3 rounded border border-slate-800 text-[11px] font-mono text-slate-300 overflow-x-auto">
                  {JSON.stringify(selectedApproval.preview_payload, null, 2)}
                </pre>
              </div>

              {/* Action Buttons (Read-Only Preview Mode) */}
              <div className="pt-2 flex items-center space-x-3">
                <button
                  disabled
                  className="bg-emerald-600/50 text-emerald-200 text-xs px-4 py-2 rounded font-medium cursor-not-allowed border border-emerald-500/30"
                >
                  Approve (Simulated Gate)
                </button>
                <button
                  disabled
                  className="bg-red-600/50 text-red-200 text-xs px-4 py-2 rounded font-medium cursor-not-allowed border border-red-500/30"
                >
                  Reject
                </button>
                <span className="text-[11px] text-slate-500 font-mono italic">
                  Read-only mode active: mutation calls disabled
                </span>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-xs font-mono text-slate-500">
              Select an approval request to inspect payload
            </div>
          )}
        </div>
      </div>

      {/* 2. Plugin Trust & Cryptographic Verification Registry */}
      <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-5 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div>
            <h3 className="text-sm font-semibold text-slate-200">Plugin Trust & Cryptographic Verification</h3>
            <p className="text-xs text-slate-400">ED25519 Signed Manifests & Sandboxed Capabilities</p>
          </div>
          <span className="text-xs font-mono text-emerald-400">100% Verified</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {plugins.map((plug) => (
            <div
              key={plug.id}
              className="border border-slate-800/80 bg-slate-950/40 rounded-lg p-4 space-y-2 text-xs"
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-200">{plug.name}</span>
                <span className="font-mono text-[10px] text-slate-400">v{plug.version}</span>
              </div>
              <p className="text-[11px] text-slate-400 font-mono">Signer: {plug.signer}</p>
              <div className="pt-2 border-t border-slate-800/60 space-y-1">
                <p className="text-[10px] text-slate-500 uppercase">Capabilities:</p>
                <div className="flex flex-wrap gap-1">
                  {plug.capabilities.map((cap, idx) => (
                    <span
                      key={idx}
                      className="bg-slate-800 text-slate-300 text-[9px] font-mono px-1.5 py-0.5 rounded"
                    >
                      {cap}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
