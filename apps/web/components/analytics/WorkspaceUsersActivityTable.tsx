// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_analytics_workspace_users_activity_table"
// purpose: "Workspace Users Activity Table displaying members, activity counts and last active timestamps"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React from 'react';

interface UserActivityItem {
  user_id?: string;
  name?: string;
  email?: string;
  activity_count?: number;
  count?: number;
  last_active?: string;
  timestamp?: string;
  role?: string;
}

interface WorkspaceUsersActivityTableProps {
  users: UserActivityItem[];
}

export function WorkspaceUsersActivityTable({ users = [] }: WorkspaceUsersActivityTableProps) {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 shadow-xl backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Team Activity</h3>
        <span className="text-xs text-slate-400 font-mono">{users.length} active users</span>
      </div>

      {users.length === 0 ? (
        <div className="py-8 flex items-center justify-center text-slate-500 text-sm border border-dashed border-slate-800 rounded-lg">
          No user activity recorded for this period
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="text-xs uppercase bg-slate-950/60 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">User</th>
                <th className="py-3 px-4">Role</th>
                <th className="py-3 px-4 text-center">Events Count</th>
                <th className="py-3 px-4 text-right">Last Active</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
              {users.map((u, i) => {
                const count = u.activity_count ?? u.count ?? 0;
                const userId = u.user_id || `user_${i + 1}`;
                const name = u.name || userId;
                const lastActive = u.last_active || u.timestamp || 'Just now';

                return (
                  <tr key={i} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 font-sans font-medium text-white flex items-center gap-2">
                      <div className="w-6 h-6 rounded-full bg-blue-600/30 text-blue-400 flex items-center justify-center text-xs font-bold font-mono">
                        {name.charAt(0).toUpperCase()}
                      </div>
                      <span>{name}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded">
                        {u.role || 'Member'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center text-cyan-400 font-bold">
                      {count}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-400">
                      {lastActive}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default WorkspaceUsersActivityTable;
