/*
# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/infrastructure/llm/gemini/client.ts"
# purpose: "Google Gemini REST Client with Mock & Live Modes."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

export interface GeminiRequestPart {
  text?: string;
  inlineData?: {
    mimeType: string;
    data: string; // base64
  };
}

export interface GeminiRequestPayload {
  contents: {
    role?: string;
    parts: GeminiRequestPart[];
  }[];
  systemInstruction?: {
    parts: { text: string }[];
  };
  generationConfig?: {
    responseMimeType?: string;
    temperature?: number;
    maxOutputTokens?: number;
  };
}

export interface GeminiResponsePayload {
  candidates?: {
    content?: {
      parts?: { text?: string }[];
    };
    finishReason?: string;
  }[];
  usageMetadata?: {
    promptTokenCount?: number;
    candidatesTokenCount?: number;
    totalTokenCount?: number;
  };
}

export interface GeminiClientOptions {
  apiKey?: string;
  baseUrl?: string;
  fetchFn?: typeof fetch;
}

export class GeminiClient {
  private readonly apiKey: string;
  private readonly baseUrl: string;
  private readonly fetchFn: typeof fetch;

  constructor(options: GeminiClientOptions = {}) {
    this.apiKey = options.apiKey || process.env.GEMINI_API_KEY || '';
    this.baseUrl = options.baseUrl || 'https://generativelanguage.googleapis.com/v1beta';
    this.fetchFn = options.fetchFn || globalThis.fetch || fetch;
  }

  public async generateContent(
    model: string,
    payload: GeminiRequestPayload
  ): Promise<{ response: GeminiResponsePayload; status: number; headers: Headers }> {
    if (!this.apiKey && !process.env.VITEST) {
      throw new Error('Gemini API key is not configured (missing GEMINI_API_KEY).');
    }

    const url = `${this.baseUrl}/models/${model}:generateContent?key=${this.apiKey}`;
    const headers = new Headers({
      'Content-Type': 'application/json',
    });

    const response = await this.fetchFn(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });

    const status = response.status;
    let json: GeminiResponsePayload;

    try {
      json = (await response.json()) as GeminiResponsePayload;
    } catch (e: any) {
      throw new Error(`Failed to parse Gemini response as JSON: ${e.message}`);
    }

    return {
      response: json,
      status,
      headers: response.headers,
    };
  }
}
