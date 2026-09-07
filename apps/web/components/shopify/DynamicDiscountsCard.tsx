// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_shopify_DynamicDiscountsCard"
// purpose: "React Admin Component for Dynamic Discount Rules (DNK-ECOM-005 Phase 4)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React, { useState } from "react";
import { DynamicDiscountRule } from "../../lib/api/shopify_functions_client";

interface DynamicDiscountsCardProps {
  rules: DynamicDiscountRule[];
  onCreateDiscountRule: (rule: any) => void;
  isLoading?: boolean;
}

export const DynamicDiscountsCard: React.FC<DynamicDiscountsCardProps> = ({
  rules,
  onCreateDiscountRule,
  isLoading = false,
}) => {
  const [discountTitle, setDiscountTitle] = useState("");
  const [discountType, setDiscountType] = useState<"tiered_volume" | "b2b_wholesale" | "vip_customer">("tiered_volume");
  const [discountValue, setDiscountValue] = useState(15);
  const [minQuantity, setMinQuantity] = useState(5);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!discountTitle) return;

    onCreateDiscountRule({
      discount_title: discountTitle,
      discount_type: discountType,
      percentage_off: discountType !== "vip_customer" ? discountValue : 0,
      fixed_amount: discountType === "vip_customer" ? discountValue : 0,
      min_quantity: minQuantity,
      customer_tags: discountType === "b2b_wholesale" ? ["B2B", "Wholesale"] : ["VIP"],
    });

    setDiscountTitle("");
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-slate-100 shadow-xl">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div>
          <h3 className="text-lg font-semibold text-purple-400">Dynamic Discount Logic Engine</h3>
          <p className="text-xs text-slate-400 mt-0.5">Shopify Function Target: purchase.product-discount.run</p>
        </div>
        <span className="px-2.5 py-1 text-xs font-mono bg-purple-950/60 text-purple-300 border border-purple-800/60 rounded-md">
          {rules.length} Rules Active
        </span>
      </div>

      <form onSubmit={handleSubmit} className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-3">
        <input
          type="text"
          placeholder="Discount Title (e.g. 15% Volume Off)"
          value={discountTitle}
          onChange={(e) => setDiscountTitle(e.target.value)}
          className="bg-slate-800/80 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-purple-500"
        />
        <select
          value={discountType}
          onChange={(e: any) => setDiscountType(e.target.value)}
          className="bg-slate-800/80 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-purple-500"
        >
          <option value="tiered_volume">Tiered Volume</option>
          <option value="b2b_wholesale">B2B Wholesale</option>
          <option value="vip_customer">VIP Fixed</option>
        </select>
        <input
          type="number"
          placeholder="Discount Value (% or $)"
          value={discountValue}
          onChange={(e) => setDiscountValue(Number(e.target.value))}
          className="bg-slate-800/80 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-purple-500"
        />
        <button
          type="submit"
          disabled={isLoading || !discountTitle}
          className="bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg px-4 py-2 transition-all"
        >
          {isLoading ? "Saving..." : "+ Add Discount"}
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
                <span className="text-sm font-medium text-slate-200">{rule.discount_title}</span>
                <span className="text-2xs px-2 py-0.5 rounded bg-purple-900/50 text-purple-300 font-mono">
                  {rule.discount_type}
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono mt-1">
                Value: {rule.discount_value} {rule.discount_value_type === "percentage" ? "%" : "USD"}
              </p>
            </div>
            <div className="text-right">
              <span className="inline-block px-2 py-1 text-xs font-mono rounded bg-purple-950/40 text-purple-400 border border-purple-900/50">
                Active
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
