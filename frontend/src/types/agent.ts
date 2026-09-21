export type AgentStatus = "answered" | "rejected" | "not_configured";

export interface AskRequest {
  question: string;
  user_role?: string | null;
}

export interface AskResponse {
  answer: string;
  sql: string | null;
  sources: string[];
  status: AgentStatus;
  guardrail_violations: string[];
}

export interface HealthResponse {
  status: "ok";
  env: string;
}

export interface ValidationIssue {
  loc: Array<string | number>;
  msg: string;
  type: string;
}

export interface ApiErrorResponse {
  detail?: string | ValidationIssue[];
}
