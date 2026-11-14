// Typed calls to the API. Same origin: Caddy serves the views and proxies /api, so the session cookie just works.
import type { CommandIn, CommandResult, ContractOut, EventEnvelope, Job, Me, Overview, Recommendation, Refusal, TechOut } from "./types";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
    readonly refusal?: Refusal,
  ) {
    super(message);
  }
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    credentials: "same-origin",
    headers: { "content-type": "application/json" },
    ...init,
  });
  if (res.status === 204) return undefined as T;
  const body: unknown = await res.json().catch(() => null);
  if (!res.ok) {
    const refusal = body && typeof body === "object" && "reason" in body ? (body as Refusal) : undefined;
    const detail = body && typeof body === "object" && "detail" in body ? String((body as { detail: unknown }).detail) : "";
    throw new ApiError(res.status, refusal?.reason ?? (detail || `The server answered ${res.status}`), refusal);
  }
  return body as T;
}

export const api = {
  me: () => call<Me>("/api/auth/me"),
  login: (email: string, password: string) =>
    call<Me>("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  logout: () => call<void>("/api/auth/logout", { method: "POST" }),
  jobs: (query = "") => call<Job[]>(`/api/jobs${query}`),
  overview: () => call<Overview>("/api/overview"),
  events: (jobId: string) => call<EventEnvelope[]>(`/api/jobs/${jobId}/events`),
  contract: (jobId: string) => call<ContractOut>(`/api/jobs/${jobId}/contract`),
  recommendation: (jobId: string) => call<Recommendation>(`/api/jobs/${jobId}/recommendation`),
  techs: () => call<TechOut[]>("/api/techs"),
  simulateRequest: () => call<CommandResult>("/api/intake/simulate", { method: "POST" }),
  command: (jobId: string, cmd: CommandIn) =>
    call<CommandResult>(`/api/jobs/${jobId}/commands`, { method: "POST", body: JSON.stringify(cmd) }),
};
