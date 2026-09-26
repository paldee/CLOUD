export type AgentStatus = "answered" | "rejected" | "not_configured";

export interface AskRequest {
  question: string;
  user_role?: string | null;
}

export interface ChartDataset {
  label: string;
  data: Array<number | null>;
}

export interface ChartSpec {
  type: "bar" | "line";
  title: string;
  labels: string[];
  datasets: ChartDataset[];
  total_points: number;
}

export interface AskResponse {
  answer: string;
  sql: string | null;
  sources: string[];
  status: AgentStatus;
  guardrail_violations: string[];
  visualization: ChartSpec | null;
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
