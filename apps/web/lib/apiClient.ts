// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_lib_api_client_session"
// purpose: "Secure client-side API transport with JWT session and zero-secret bundle exposure"
// author: "DNK-e.com Maksym & Gerych"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-04"
// --- END DNK-MRH-HEADER ---

export class ApiClient {
  private jwtToken: string | null = null;

  constructor(initialToken?: string) {
    if (initialToken) {
      this.jwtToken = initialToken;
    }
  }

  setToken(token: string | null): void {
    this.jwtToken = token;
  }

  getToken(): string | null {
    return this.jwtToken;
  }

  async authenticate(email: string, password: string): Promise<void> {
    const response = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      throw new Error(`Authentication failed: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    this.jwtToken = data.jwt_token || data.access_token || null;
  }

  async request(endpoint: string, options: RequestInit = {}): Promise<Response> {
    const headers: Record<string, string> = {
      ...((options.headers as Record<string, string>) || {}),
    };

    if (this.jwtToken) {
      headers["Authorization"] = `Bearer ${this.jwtToken}`;
    }

    const response = await fetch(`/api/v1${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 412 || response.status === 503) {
      // Secrets missing on backend - strict fail without fallback
      throw new Error("Backend secrets not configured");
    }

    return response;
  }
}

export const apiClient = new ApiClient();
