// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_shopify_FunctionsEvaluationSandbox"
// purpose: "Interactive Sandbox for Shopify Functions Wasm execution & metrics (DNK-ECOM-005 Phase 4)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React, { useState } from "react";
import { WasmEvaluationResult } from "../../lib/api/shopify_functions_client";

interface FunctionsEvaluationSandboxProps {
  onEvaluate: (apiType: string, payload: Record<string, any>) => Promise<WasmEvaluationResult>;
  isLoading?: boolean;
}

export const FunctionsEvaluationSandbox: React.FC<FunctionsEvaluationSandboxProps> = ({
  onEvaluate,
  isLoading = false,
}) => {
  const [apiType, setApiType] = useState("cart_transform");
  const [inputJson, setInputJson] = useState(`{
  "cart": {
    "lines": [
      {
        "id": "gid://shopify/CartLine/1",
        "quantity": 2,
        "merchandise": {
          "id": "gid://shopify/ProductVariant/bundle-1"
        }
      }
    ]
  }
}`);
  const [result, setResult] = useState<WasmEvaluationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRunEvaluation = async () => {
    setError(null);
    try {
      const parsed = JSON.parse(inputJson);
      const res = await onEvaluate(apiType, parsed);
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Invalid JSON syntax");
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-slate-100 shadow-xl">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div>
          <h3 className="text-lg font-semibold text-cyan-400">Shopify Functions Sandbox Runner</h3>
          <p className="text-xs text-slate-400 mt-0.5">Wasm Sandbox: CPU limit ≤5ms, Memory limit ≤10MB</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={apiType}
            onChange={(e) => setApiType(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-cyan-300 font-mono focus:outline-none"
          >
            <option value="cart_transform">Cart Transform (purchase.cart-transform.run)</option>
            <option value="product_discounts">Product Discounts (purchase.product-discount.run)</option>
            <option value="delivery_customization">Delivery Customization (purchase.delivery-customization.run)</option>
            <option value="payment_customization">Payment Customization (purchase.payment-customization.run)</option>
          </select>
          <button
            onClick={handleRunEvaluation}
            disabled={isLoading}
            className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg px-3 py-1.5 transition-all"
          >
            {isLoading ? "Executing Wasm..." : "▶ Run Sandbox"}
          </button>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-mono text-slate-400 mb-1">Input Payload (JSON)</label>
          <textarea
            value={inputJson}
            onChange={(e) => setInputJson(e.target.value)}
            rows={10}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div>
          <label className="block text-xs font-mono text-slate-400 mb-1">Wasm Output & Metrics</label>
          {result ? (
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs font-mono space-y-2">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="text-emerald-400 font-semibold">Status: {result.status.toUpperCase()}</span>
                <div className="flex items-center gap-3 text-slate-400 text-2xs">
                  <span>⏱ {result.execution_time_ms.toFixed(2)}ms</span>
                  <span>💾 {(result.memory_usage_bytes / 1024).toFixed(1)}KB</span>
                </div>
              </div>
              <pre className="text-slate-300 max-h-44 overflow-y-auto pt-1">
                {JSON.stringify(result.output, null, 2)}
              </pre>
            </div>
          ) : (
            <div className="bg-slate-950 border border-dashed border-slate-800 rounded-lg p-8 text-center text-xs text-slate-500">
              {error ? <span className="text-rose-400">{error}</span> : "Run sandbox to view Wasm execution metrics"}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
