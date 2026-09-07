// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_platform_edge_routing_rules_table"
// purpose: "React Component for Edge Routing Rules Table & Cloud Provider Script Preview (DNK-PLATFORM-SCALE-003)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React from "react";
import { EdgeRoutingRule } from "../../lib/api/platform_regions_client";

interface Props {
  rules: EdgeRoutingRule[];
}

export const EdgeRoutingRulesTable: React.FC<Props> = ({ rules }) => {
  return (
    <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg text-slate-100 shadow-sm mt-4">
      <h3 className="text-lg font-semibold mb-3 text-cyan-400">⚡ Edge Routing Rules</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-800 text-slate-400 text-xs uppercase">
            <tr>
              <th className="px-4 py-2">Rule Name</th>
              <th className="px-4 py-2">Match Type</th>
              <th className="px-4 py-2">Geo Values</th>
              <th className="px-4 py-2">Target Region</th>
              <th className="px-4 py-2">Priority</th>
              <th className="px-4 py-2">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {rules.map((rule) => (
              <tr key={rule.id} className="hover:bg-slate-800/50">
                <td className="px-4 py-3 font-medium text-slate-200">{rule.rule_name}</td>
                <td className="px-4 py-3">
                  <span className="px-2 py-0.5 text-xs bg-cyan-950 text-cyan-300 border border-cyan-800 rounded">
                    {rule.geo_match_type}
                  </span>
                </td>
                <td className="px-4 py-3 text-xs font-mono">{rule.geo_values.join(", ")}</td>
                <td className="px-4 py-3 font-mono text-emerald-400">{rule.target_region}</td>
                <td className="px-4 py-3">{rule.priority}</td>
                <td className="px-4 py-3">
                  {rule.enabled ? (
                    <span className="text-xs text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800">
                      Active
                    </span>
                  ) : (
                    <span className="text-xs text-slate-500 bg-slate-800 px-2 py-0.5 rounded">Disabled</span>
                  )}
                </td>
              </tr>
            ))}
            {rules.length === 0 && (
              <tr>
                <td colSpan={6} className="text-center py-4 text-slate-500">
                  No edge routing rules configured
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
