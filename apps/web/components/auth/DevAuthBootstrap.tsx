// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_auth_DevAuthBootstrap"
// purpose: "Development Authentication Bootstrap and Workspace UUID switcher component (DNK-VISUAL-OS-003-A)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.2.0"
// updated_at: "2026-08-26"
// --- END DNK-MRH-HEADER ---

"use client";

import React, { useState, useEffect } from "react";

export interface DevSession {
  user_id: string;
  name: string;
  role: string;
  workspace_id: string; // RFC4122 non-zero UUID
  workspace_label: string;
  token: string;
}

export const WORKSPACES_REGISTRY = [
  {
    id: "11111111-2222-4333-8444-555555555555",
    name: "DNK Core Production",
    label: "ws-alpha-001",
    role: "Owner",
  },
  {
    id: "22222222-3333-4444-8555-666666666666",
    name: "DNK Shopify Ecosystem",
    label: "ws-shopify-001",
    role: "Admin",
  },
];

interface DevAuthBootstrapProps {
  onSessionChange?: (session: DevSession | null) => void;
}

export function DevAuthBootstrap({ onSessionChange }: DevAuthBootstrapProps) {
  // Fail-closed: initial session is strictly null (unauthenticated)
  const [session, setSession] = useState<DevSession | null>(null);
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [selectedWsId, setSelectedWsId] = useState<string>(WORKSPACES_REGISTRY[0].id);
  const [inputToken, setInputToken] = useState<string>("");
  const [userName, setUserName] = useState<string>("Maxim (Primary Supervisor)");
  const [userId, setUserId] = useState<string>("usr-maxim-001");

  // In production mode, DevAuthBootstrap is completely disabled
  const isProduction = process.env.NODE_ENV === "production";

  useEffect(() => {
    if (isProduction) {
      return;
    }
    try {
      const stored = typeof window !== "undefined" && typeof sessionStorage !== "undefined"
        ? sessionStorage.getItem("dnk_dev_session")
        : null;
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed && parsed.workspace_id && parsed.token) {
          setSession(parsed);
          if (onSessionChange) onSessionChange(parsed);
          return;
        }
      }
      // Fail-closed: empty storage remains unauthenticated. No automatic token injection.
      setSession(null);
      if (onSessionChange) onSessionChange(null);
    } catch (e) {
      console.warn("Failed to parse dnk_dev_session from sessionStorage:", e);
      setSession(null);
      if (onSessionChange) onSessionChange(null);
    }
  }, [onSessionChange, isProduction]);

  if (isProduction) {
    return null;
  }

  const handleSignIn = (e: React.FormEvent) => {
    e.preventDefault();
    const tokenToUse = inputToken.trim() || "dnk-dev-token";
    const ws = WORKSPACES_REGISTRY.find((w) => w.id === selectedWsId) || WORKSPACES_REGISTRY[0];
    const newSession: DevSession = {
      user_id: userId.trim() || "usr-maxim-001",
      name: userName.trim() || "Maxim (Primary Supervisor)",
      role: ws.role,
      workspace_id: ws.id,
      workspace_label: ws.label,
      token: tokenToUse,
    };
    try {
      if (typeof sessionStorage !== "undefined") {
        sessionStorage.setItem("dnk_dev_session", JSON.stringify(newSession));
      }
    } catch (err) {
      console.error("Failed to persist dnk_dev_session:", err);
    }
    setSession(newSession);
    setIsOpen(false);
    if (onSessionChange) onSessionChange(newSession);
  };

  const handleSignOut = () => {
    try {
      if (typeof sessionStorage !== "undefined") {
        sessionStorage.removeItem("dnk_dev_session");
      }
    } catch (err) {
      console.error("Failed to remove dnk_dev_session:", err);
    }
    setSession(null);
    setIsOpen(false);
    if (onSessionChange) onSessionChange(null);
  };

  const handleWorkspaceSwitch = (wsId: string) => {
    if (!session) return;
    const ws = WORKSPACES_REGISTRY.find((w) => w.id === wsId);
    if (!ws) return;
    const updated: DevSession = {
      ...session,
      workspace_id: ws.id,
      workspace_label: ws.label,
      role: ws.role,
    };
    try {
      if (typeof sessionStorage !== "undefined") {
        sessionStorage.setItem("dnk_dev_session", JSON.stringify(updated));
      }
    } catch (err) {
      console.error("Failed to update dnk_dev_session:", err);
    }
    setSession(updated);
    if (onSessionChange) onSessionChange(updated);
  };

  return (
    <div className="relative inline-block text-left font-sans text-xs">
      <div className="flex items-center space-x-2">
        {session ? (
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="flex items-center space-x-2 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 rounded-md px-3 py-1.5 text-slate-200 transition-colors"
          >
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="font-mono text-emerald-400">{session.workspace_label}</span>
            <span className="text-slate-400">({session.role})</span>
            <svg className="h-3 w-3 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        ) : (
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="flex items-center space-x-2 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 rounded-md px-3 py-1.5 text-amber-300 transition-colors"
          >
            <span className="h-2 w-2 rounded-full bg-amber-400" />
            <span className="font-medium">Dev Auth: Unauthenticated</span>
            <svg className="h-3 w-3 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        )}
      </div>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 rounded-lg bg-slate-900 border border-slate-700 shadow-xl p-3 z-50 space-y-3">
          <div className="border-b border-slate-800 pb-2">
            <h4 className="font-semibold text-slate-100">Dev Auth Bootstrap</h4>
            <p className="text-[11px] text-slate-400">RFC4122 Workspace Tenancy & Mock Auth</p>
          </div>

          {session ? (
            <div className="space-y-3">
              <div className="space-y-1">
                <span className="text-[10px] uppercase font-mono text-slate-400">Switch Workspace:</span>
                {WORKSPACES_REGISTRY.map((ws) => (
                  <button
                    key={ws.id}
                    onClick={() => {
                      handleWorkspaceSwitch(ws.id);
                      setIsOpen(false);
                    }}
                    className={`w-full text-left px-2.5 py-2 rounded text-xs transition-colors flex flex-col space-y-0.5 ${
                      session.workspace_id === ws.id
                        ? "bg-emerald-500/10 border border-emerald-500/30 text-emerald-400"
                        : "hover:bg-slate-800 text-slate-300"
                    }`}
                  >
                    <div className="flex items-center justify-between font-medium">
                      <span>{ws.name}</span>
                      <span className="font-mono text-[10px]">{ws.label}</span>
                    </div>
                    <span className="font-mono text-[10px] text-slate-400 truncate">{ws.id}</span>
                  </button>
                ))}
              </div>

              <div className="border-t border-slate-800 pt-2 text-[10px] text-slate-400 font-mono flex justify-between items-center">
                <span>User: {session.name}</span>
                <button
                  onClick={handleSignOut}
                  className="px-2 py-1 bg-red-500/20 hover:bg-red-500/30 border border-red-500/40 text-red-300 rounded text-[10px] font-sans transition-colors"
                >
                  Sign Out
                </button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSignIn} className="space-y-3">
              <div className="space-y-1">
                <label className="text-[10px] uppercase font-mono text-slate-400">Select Workspace:</label>
                <div className="space-y-1">
                  {WORKSPACES_REGISTRY.map((ws) => (
                    <button
                      key={ws.id}
                      type="button"
                      onClick={() => setSelectedWsId(ws.id)}
                      className={`w-full text-left px-2.5 py-1.5 rounded text-xs transition-colors flex flex-col ${
                        selectedWsId === ws.id
                          ? "bg-emerald-500/10 border border-emerald-500/30 text-emerald-400"
                          : "hover:bg-slate-800 text-slate-300 border border-transparent"
                      }`}
                    >
                      <div className="flex items-center justify-between font-medium">
                        <span>{ws.name}</span>
                        <span className="font-mono text-[10px]">{ws.label}</span>
                      </div>
                      <span className="font-mono text-[10px] text-slate-400 truncate">{ws.id}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] uppercase font-mono text-slate-400">Dev Mock Token:</label>
                <input
                  type="text"
                  value={inputToken}
                  onChange={(e) => setInputToken(e.target.value)}
                  placeholder="dnk-dev-token"
                  className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1 text-slate-200 text-xs font-mono focus:outline-none focus:border-emerald-500"
                />
              </div>

              <button
                type="submit"
                className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-medium py-1.5 rounded text-xs transition-colors shadow-sm"
              >
                Sign In (Dev Mock)
              </button>
            </form>
          )}
        </div>
      )}
    </div>
  );
}
