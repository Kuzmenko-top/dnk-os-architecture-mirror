// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_shopify_CartTransformRulesCard"
// purpose: "React Admin Component for Cart Transform & Bundle Expansion Rules (DNK-ECOM-005 Phase 4)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React, { useState } from "react";
import { CartTransformRule } from "../../lib/api/shopify_functions_client";

interface CartTransformRulesCardProps {
  rules: CartTransformRule[];
  onCreateBundleRule: (rule: any) => void;
  isLoading?: boolean;
}

export const CartTransformRulesCard: React.FC<CartTransformRulesCardProps> = ({
  rules,
  onCreateBundleRule,
  isLoading = false,
}) => {
  const [ruleName, setRuleName] = useState("");
  const [parentVariantId, setParentVariantId] = useState("");
  const [minQuantity, setMinQuantity] = useState(1);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!ruleName || !parentVariantId) return;

    onCreateBundleRule({
      rule_name: ruleName,
      parent_variant_id: parentVariantId,
      min_quantity: minQuantity,
      components: [
        { variant_id: `${parentVariantId}-part1`, quantity: 1 },
        { variant_id: `${parentVariantId}-part2`, quantity: 1 },
      ],
    });

    setRuleName("");
    setParentVariantId("");
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-slate-100 shadow-xl">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div>
          <h3 className="text-lg font-semibold text-emerald-400">Cart Transform & Bundle Expansion</h3>
          <p className="text-xs text-slate-400 mt-0.5">Shopify Function Wasm Target: purchase.cart-transform.run</p>
        </div>
        <span className="px-2.5 py-1 text-xs font-mono bg-emerald-950/60 text-emerald-300 border border-emerald-800/60 rounded-md">
          {rules.length} Rules Active
        </span>
      </div>

      <form onSubmit={handleSubmit} className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
        <input
          type="text"
          placeholder="Rule Name (e.g. Summer Bundle)"
          value={ruleName}
          onChange={(e) => setRuleName(e.target.value)}
          className="bg-slate-800/80 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
        />
        <input
          type="text"
          placeholder="Parent Variant ID (gid://shopify/...)"
          value={parentVariantId}
          onChange={(e) => setParentVariantId(e.target.value)}
          className="bg-slate-800/80 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
        />
        <button
          type="submit"
          disabled={isLoading || !ruleName || !parentVariantId}
          className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg px-4 py-2 transition-all"
        >
          {isLoading ? "Saving..." : "+ Add Bundle Rule"}
        </button>
      </form>

      <div className="mt-5 space-y-2.5">
        {rules.map((rule) => (
          <div
            key={rule.rule_id}
            className="flex items-center justify-between p-3.5 bg-slate-800/40 border border-slate-800 rounded-lg hover:border-slate-700 transition-colors"
          >
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-slate-200">{rule.rule_name}</span>
                <span className="text-2xs px-2 py-0.5 rounded bg-blue-900/50 text-blue-300 font-mono">
                  {rule.transform_type}
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono mt-1">
                Parent: {rule.trigger_criteria?.parent_variant_id || "N/A"}
              </p>
            </div>
            <div className="text-right">
              <span className="inline-block px-2 py-1 text-xs font-mono rounded bg-emerald-950/40 text-emerald-400 border border-emerald-900/50">
                {rule.operations?.length || 0} Components
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
