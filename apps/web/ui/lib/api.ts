// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/ui/lib/api.ts"
// purpose: "Universal API client for DNK OS frontend components"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["DNK-UI-GEN-003"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym & Gerych Builder"
// --- END DNK-MRH-HEADER ---

export async function apiClient<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const defaultHeaders = {
    "Content-Type": "application/json",
  };

  const response = await fetch(endpoint, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`API Error [${response.status}]: ${errorBody || response.statusText}`);
  }

  return response.json();
}

apiClient.get = function<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  return apiClient<T>(endpoint, { ...options, method: "GET" });
};

apiClient.post = function<T>(endpoint: string, body?: any, options: RequestInit = {}): Promise<T> {
  return apiClient<T>(endpoint, {
    ...options,
    method: "POST",
    body: body ? JSON.stringify(body) : undefined,
  });
};
