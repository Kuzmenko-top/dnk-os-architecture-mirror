// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_workspace_WorkspaceCollaborationBar"
// purpose: "Live Multi-User Presence, Resource Locks & Invitation Header for Visual Workspace (DNK-VISUAL-OS-003)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-27"
// --- END DNK-MRH-HEADER ---

"use client";

import React, { useState, useEffect } from "react";

export interface ActiveUser {
  userId: string;
  displayName: string;
  role: "admin" | "member" | "developer" | "viewer";
  avatarColor: string;
  status: "online" | "idle" | "editing";
  activeNodeId?: string;
}

export interface WorkspaceCollaborationBarProps {
  workspaceId: string;
  currentUserId?: string;
  activeUsers?: ActiveUser[];
  heldLocksCount?: number;
  onInviteClick?: () => void;
  onSwitchWorkspace?: (newWorkspaceId: string) => void;
}

export const WorkspaceCollaborationBar: React.FC<WorkspaceCollaborationBarProps> = ({
  workspaceId,
  currentUserId = "usr_current",
  activeUsers = [
    { userId: "usr_maksym", displayName: "Maksym (Owner)", role: "admin", avatarColor: "#3B82F6", status: "online" },
    { userId: "usr_gerych", displayName: "Gerych (AI Chief)", role: "developer", avatarColor: "#10B981", status: "editing", activeNodeId: "node_engine_occ" },
    { userId: "usr_auditor", displayName: "Auditor Bot", role: "viewer", avatarColor: "#8B5CF6", status: "idle" }
  ],
  heldLocksCount = 1,
  onInviteClick,
  onSwitchWorkspace
}) => {
  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<"member" | "developer" | "viewer">("developer");
  const [inviteSuccess, setInviteSuccess] = useState(false);

  const handleSendInvite = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail.trim()) return;
    // Simulated dispatch / contract
    setInviteSuccess(true);
    setTimeout(() => {
      setInviteSuccess(false);
      setIsInviteModalOpen(false);
      setInviteEmail("");
    }, 1500);
  };

  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "10px 18px",
      backgroundColor: "#0F172A",
      borderBottom: "1px solid #1E293B",
      color: "#F8FAFC",
      fontFamily: "Inter, sans-serif",
      fontSize: "13px"
    }}>
      {/* Left: Workspace Selector & Status */}
      <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#10B981", boxShadow: "0 0 8px #10B981" }} />
          <span style={{ fontWeight: 600, letterSpacing: "0.02em" }}>Workspace:</span>
          <span style={{
            backgroundColor: "#1E293B",
            padding: "3px 8px",
            borderRadius: "6px",
            color: "#38BDF8",
            fontWeight: 500,
            fontFamily: "JetBrains Mono, monospace"
          }}>
            {workspaceId}
          </span>
        </div>

        {heldLocksCount > 0 && (
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            backgroundColor: "#451A03",
            color: "#FBBF24",
            padding: "2px 8px",
            borderRadius: "6px",
            fontSize: "12px",
            border: "1px solid #78350F"
          }}>
            <span>🔒</span>
            <span>{heldLocksCount} Node Lock Active</span>
          </div>
        )}
      </div>

      {/* Right: Active Users Presence & Actions */}
      <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
        {/* Presence Avatars */}
        <div style={{ display: "flex", alignItems: "center", gap: "-6px" }}>
          <span style={{ fontSize: "12px", color: "#94A3B8", marginRight: "6px" }}>Live Presence:</span>
          <div style={{ display: "flex", flexDirection: "row", alignItems: "center" }}>
            {activeUsers.map((user, idx) => (
              <div
                key={user.userId}
                title={`${user.displayName} (${user.role}) - ${user.status}${user.activeNodeId ? ` on ${user.activeNodeId}` : ""}`}
                style={{
                  width: "28px",
                  height: "28px",
                  borderRadius: "50%",
                  backgroundColor: user.avatarColor,
                  color: "#FFFFFF",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontWeight: 700,
                  fontSize: "11px",
                  border: "2px solid #0F172A",
                  marginLeft: idx === 0 ? "0px" : "-8px",
                  cursor: "pointer",
                  position: "relative"
                }}
              >
                {user.displayName.charAt(0).toUpperCase()}
                {user.status === "editing" && (
                  <span style={{
                    position: "absolute",
                    bottom: "-2px",
                    right: "-2px",
                    width: "8px",
                    height: "8px",
                    borderRadius: "50%",
                    backgroundColor: "#EF4444",
                    border: "1px solid #0F172A"
                  }} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Invite Button */}
        <button
          onClick={() => {
            if (onInviteClick) onInviteClick();
            else setIsInviteModalOpen(true);
          }}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            backgroundColor: "#2563EB",
            color: "#FFFFFF",
            border: "none",
            borderRadius: "6px",
            padding: "5px 12px",
            fontSize: "12px",
            fontWeight: 600,
            cursor: "pointer",
            transition: "all 0.2s ease"
          }}
        >
          <span>➕</span>
          <span>Invite Member</span>
        </button>
      </div>

      {/* Invite Modal */}
      {isInviteModalOpen && (
        <div style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: "rgba(0, 0, 0, 0.75)",
          backdropFilter: "blur(4px)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 9999
        }}>
          <div style={{
            backgroundColor: "#0F172A",
            border: "1px solid #334155",
            borderRadius: "12px",
            padding: "24px",
            width: "420px",
            boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.5)"
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px" }}>
              <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 600, color: "#F8FAFC" }}>
                👥 Invite to Workspace {workspaceId}
              </h3>
              <button
                onClick={() => setIsInviteModalOpen(false)}
                style={{ background: "transparent", border: "none", color: "#94A3B8", fontSize: "18px", cursor: "pointer" }}
              >
                ✕
              </button>
            </div>

            {inviteSuccess ? (
              <div style={{
                backgroundColor: "#064E3B",
                color: "#6EE7B7",
                padding: "12px",
                borderRadius: "8px",
                textAlign: "center",
                fontWeight: 500
              }}>
                ✅ Invitation email sent successfully!
              </div>
            ) : (
              <form onSubmit={handleSendInvite} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "12px", color: "#94A3B8", marginBottom: "6px" }}>Email Address</label>
                  <input
                    type="email"
                    required
                    placeholder="developer@dnk-e.com"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    style={{
                      width: "100%",
                      boxSizing: "border-box",
                      backgroundColor: "#1E293B",
                      border: "1px solid #334155",
                      color: "#F8FAFC",
                      borderRadius: "6px",
                      padding: "8px 12px",
                      fontSize: "13px"
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "12px", color: "#94A3B8", marginBottom: "6px" }}>Role Access</label>
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value as any)}
                    style={{
                      width: "100%",
                      backgroundColor: "#1E293B",
                      border: "1px solid #334155",
                      color: "#F8FAFC",
                      borderRadius: "6px",
                      padding: "8px 12px",
                      fontSize: "13px"
                    }}
                  >
                    <option value="developer">Developer (Full Edit & OCC Commit)</option>
                    <option value="member">Member (Read & Node Drafting)</option>
                    <option value="viewer">Viewer (Read-Only Realtime Presence)</option>
                  </select>
                </div>

                <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "10px" }}>
                  <button
                    type="button"
                    onClick={() => setIsInviteModalOpen(false)}
                    style={{
                      backgroundColor: "transparent",
                      border: "1px solid #475569",
                      color: "#CBD5E1",
                      borderRadius: "6px",
                      padding: "6px 14px",
                      fontSize: "12px",
                      cursor: "pointer"
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    style={{
                      backgroundColor: "#2563EB",
                      border: "none",
                      color: "#FFFFFF",
                      borderRadius: "6px",
                      padding: "6px 16px",
                      fontSize: "12px",
                      fontWeight: 600,
                      cursor: "pointer"
                    }}
                  >
                    Send Invitation
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
