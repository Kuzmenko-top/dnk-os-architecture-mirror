// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_lib_api_shopify_functions_client"
// purpose: "TypeScript client for Shopify Functions & Wasm Engine API (DNK-ECOM-005 Phase 4)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

export interface CartTransformRule {
  rule_id: string;
  rule_name: string;
  transform_type: "bundle_expand" | "bundle_merge" | "price_override" | "component_split";
  trigger_criteria: Record<string, any>;
  operations: Array<Record<string, any>>;
  enabled: boolean;
}

export interface DynamicDiscountRule {
  rule_id: string;
  discount_title: string;
  discount_type: "tiered_volume" | "b2b_wholesale" | "vip_customer" | "bxgy";
  conditions: Record<string, any>;
  discount_value_type: "percentage" | "fixed_amount";
  discount_value: number;
  enabled: boolean;
}

export interface DeliveryCustomizationRule {
  rule_id: string;
  rule_name: string;
  action: "hide" | "rename" | "move";
  target_delivery_methods: string[];
  parameters?: Record<string, any>;
  enabled: boolean;
}

export interface WasmEvaluationResult {
  invocation_id: string;
  api_type: string;
  status: "success" | "error" | "timeout" | "memory_exceeded";
  output: Record<string, any>;
  execution_time_ms: number;
  memory_usage_bytes: number;
  error_message?: string;
}

export class ShopifyFunctionsClient {
  private baseUrl: string;

  constructor(baseUrl: string = "/api/v1/shopify/functions") {
    this.baseUrl = baseUrl;
  }

  async getHealth(): Promise<{ status: string; supported_targets: string[] }> {
    const res = await fetch(`${this.baseUrl}/health`);
    return res.json();
  }

  async listCartTransformRules(workspaceId: string): Promise<CartTransformRule[]> {
    const res = await fetch(`${this.baseUrl}/cart-transform/rules?workspace_id=${encodeURIComponent(workspaceId)}`);
    const data = await res.json();
    return data.rules || [];
  }

  async createBundleExpansionRule(payload: {
    workspace_id: string;
    rule_name: string;
    parent_variant_id: string;
    components: Array<{ variant_id: string; quantity: number; price_override?: any }>;
    min_quantity?: number;
  }): Promise<{ status: string; rule: CartTransformRule }> {
    const res = await fetch(`${this.baseUrl}/cart-transform/rules/bundle`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return res.json();
  }

  async listDiscountRules(workspaceId: string): Promise<DynamicDiscountRule[]> {
    const res = await fetch(`${this.baseUrl}/discounts/rules?workspace_id=${encodeURIComponent(workspaceId)}`);
    const data = await res.json();
    return data.rules || [];
  }

  async createDiscountRule(payload: {
    workspace_id: string;
    discount_title: string;
    discount_type: string;
    min_quantity?: number;
    percentage_off?: number;
    customer_tags?: string[];
    fixed_amount?: number;
  }): Promise<{ status: string; rule: DynamicDiscountRule }> {
    const res = await fetch(`${this.baseUrl}/discounts/rules`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return res.json();
  }

  async evaluateFunction(payload: {
    workspace_id: string;
    api_type: string;
    input_payload: Record<string, any>;
  }): Promise<WasmEvaluationResult> {
    const res = await fetch(`${this.baseUrl}/evaluate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return res.json();
  }
}

export const shopifyFunctionsClient = new ShopifyFunctionsClient();
