import type {
  ApiErrorResponse,
  AskRequest,
  AskResponse,
  HealthResponse,
} from "../types/agent";

export interface AgentApiOptions {
  baseUrl: string;
  fetchImpl?: typeof fetch;
}

export class AgentApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly details?: ApiErrorResponse,
  ) {
    super(message);
    this.name = "AgentApiError";
  }
}

export function createAgentApi({ baseUrl, fetchImpl = fetch }: AgentApiOptions) {
  const normalizedBaseUrl = baseUrl.replace(/\/$/, "");

  async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetchImpl(`${normalizedBaseUrl}${path}`, init);
    const body = (await response.json().catch(() => undefined)) as
      | T
      | ApiErrorResponse
      | undefined;

    if (!response.ok) {
      throw new AgentApiError(
        `Agent API request failed with status ${response.status}`,
        response.status,
        body as ApiErrorResponse | undefined,
      );
    }

    return body as T;
  }

  return {
    health(signal?: AbortSignal): Promise<HealthResponse> {
      return request<HealthResponse>("/health", { signal });
    },

    ask(payload: AskRequest, signal?: AbortSignal): Promise<AskResponse> {
      return request<AskResponse>("/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal,
      });
    },
  };
}
