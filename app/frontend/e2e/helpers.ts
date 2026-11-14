import { expect, type APIRequestContext, type Page, type PlaywrightWorkerArgs } from "@playwright/test";
import { readFileSync } from "node:fs";

export const logins = Object.fromEntries(
  readFileSync(process.env.E2E_LOGINS ?? "", "utf8")
    .split("\n")
    .filter((l) => l.includes("="))
    .map((l) => [l.slice(0, l.indexOf("=")), l.slice(l.indexOf("=") + 1).trim()]),
) as Record<string, string>;

export async function signIn(page: Page, email: string) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(logins[email] ?? "");
  await page.getByRole("button", { name: "Sign in" }).click();
}

export async function apiAs(request: APIRequestContext, email: string) {
  const r = await request.post("/api/auth/login", { data: { email, password: logins[email] } });
  expect(r.ok()).toBeTruthy();
}

export function watchConsole(page: Page): string[] {
  const errors: string[] = [];
  // The one expected failure: before sign-in, the session check (/api/auth/me) answers 401 by design.
  page.on("console", (m) => m.type() === "error" && !/status of 401/.test(m.text()) && errors.push(m.text()));
  page.on("pageerror", (e) => errors.push(e.message));
  return errors;
}

// One signed-in API session per account per worker, reused: a person stays signed in, and the login limit (10 a
// minute per account and address) is for guessing, not for a test suite.
const sessions = new Map<string, Promise<APIRequestContext>>();

export function office(playwright: PlaywrightWorkerArgs["playwright"], baseURL: string, email: string): Promise<APIRequestContext> {
  let ctx = sessions.get(email);
  if (!ctx) {
    ctx = (async () => {
      const c = await playwright.request.newContext({ baseURL, extraHTTPHeaders: { Origin: baseURL } });
      await apiAs(c, email);
      return c;
    })();
    sessions.set(email, ctx);
  }
  return ctx;
}

type Ready = { id: string; number: number; last_event_id: number; requires_approval: boolean };

/** A fresh job, ready for dispatch: a new request drafted, qualified, approved by the client if a rule asks, and
 * approved for dispatch. Tests make their own rather than use up the seed's handful. */
export async function makeReadyJob(playwright: PlaywrightWorkerArgs["playwright"], baseURL: string): Promise<Ready> {
  const request = await office(playwright, baseURL, "coord@ofs.com");
  let made = await request.post("/api/intake/simulate");
  for (let i = 0; made.status() === 429 && i < 3; i++) {
    await new Promise((r) => setTimeout(r, 3100)); // one new request every few seconds per person
    made = await request.post("/api/intake/simulate");
  }
  expect(made.ok(), await made.text()).toBeTruthy();
  const id = ((await made.json()) as { job: Ready }).job.id;
  const step = async (command: string, payload: object = {}) => {
    const job = (await (await request.get(`/api/jobs/${id}`)).json()) as Ready;
    const r = await request.post(`/api/jobs/${id}/commands`, { data: { command, expected_event_id: job.last_event_id, payload } });
    expect(r.ok(), await r.text()).toBeTruthy();
    return job;
  };
  const job = await step("qualify");
  if (job.requires_approval) {
    await step("request_client_approval");
    await step("record_client_approval", { by: "Client facilities manager", client_ref: "APR-E2E" });
  }
  await step("approve_for_dispatch");
  return (await (await request.get(`/api/jobs/${id}`)).json()) as Ready;
}
