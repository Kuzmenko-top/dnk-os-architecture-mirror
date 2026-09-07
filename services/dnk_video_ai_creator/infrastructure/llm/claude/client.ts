/*
# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/infrastructure/llm/claude/client.ts"
# purpose: "Anthropic Claude REST Client with Mock & Live Modes."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

export interface ClaudeMessagePart {
  type: 'text' | 'image';
  text?: string;
  source?: {
    type: 'base64';
    media_type: string;
    data: string;
  };
}

export interface ClaudeRequestPayload {
  model: string;
  messages: {
    role: 'user' | 'assistant';
    content: string | ClaudeMessagePart[];
  }[];
  system?: string;
  max_tokens: number;
  temperature?: number;
}

export interface ClaudeResponsePayload {
  id?: string;
  type?: string;
  role?: string;
  content?: {
    type?: 'text';
    text?: string;
  }[];
  model?: string;
  stop_reason?: 'end_turn' | 'max_tokens' | 'stop_sequence';
  usage?: {
    input_tokens?: number;
    output_tokens?: number;
  };
  error?: {
    type?: string;
    message?: string;
  };
}

export interface ClaudeClientOptions {
  apiKey?: string;
  baseUrl?: string;
  fetchFn?: typeof fetch;
}

export class ClaudeClient {
  private readonly apiKey: string;
  private readonly baseUrl: string;
  private readonly fetchFn: typeof fetch;

  constructor(options: ClaudeClientOptions = {}) {
    this.apiKey = options.apiKey || process.env.ANTHROPIC_API_KEY || '';
    this.baseUrl = options.baseUrl || 'https://api.anthropic.com/v1';
    this.fetchFn = options.fetchFn || globalThis.fetch || fetch;
  }

  public async createMessage(
    payload: ClaudeRequestPayload
  ): Promise<{ response: ClaudeResponsePayload; status: number; headers: Headers }> {
    if (!this.apiKey && !process.env.VITEST) {
      throw new Error('Claude API key is not configured (missing ANTHROPIC_API_KEY).');
    }

    const url = `${this.baseUrl}/messages`;
    const headers = new Headers({
      'Content-Type': 'application/json',
      'x-api-key': this.apiKey,
      'anthropic-version': '2023-06-01',
    });

    const response = await this.fetchFn(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });

    const status = response.status;
    let json: ClaudeResponsePayload;

    try {
      json = (await response.json()) as ClaudeResponsePayload;
    } catch (e: any) {
      throw new Error(`Failed to parse Claude response as JSON: ${e.message}`);
    }

    return {
      response: json,
      status,
      headers: response.headers,
    };
  }
}
