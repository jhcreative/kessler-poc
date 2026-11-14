// POC-06 in a real browser (PP-14): sign in, the overview fills from the API, and a change made by another role
// appears in it within a second, with no reload (G1, G3).
import { expect, test, type APIRequestContext, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";

const logins = Object.fromEntries(
  readFileSync(process.env.E2E_LOGINS ?? "", "utf8")
    .split("\n")
    .filter((l) => l.includes("="))
    .map((l) => [l.slice(0, l.indexOf("=")), l.slice(l.indexOf("=") + 1).trim()]),
) as Record<string, string>;

async function signIn(page: Page, email: string) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(logins[email] ?? "");
  await page.getByRole("button", { name: "Sign in" }).click();
}

async function apiAs(request: APIRequestContext, email: string) {
  const r = await request.post("/api/auth/login", { data: { email, password: logins[email] } });
  expect(r.ok()).toBeTruthy();
}

function watchConsole(page: Page): string[] {
  const errors: string[] = [];
  // The one expected failure: before sign-in, the session check (/api/auth/me) answers 401 by design.
  page.on("console", (m) => m.type() === "error" && !/status of 401/.test(m.text()) && errors.push(m.text()));
  page.on("pageerror", (e) => errors.push(e.message));
  return errors;
}

test("the exec signs in to a full, live overview", async ({ page }) => {
  const errors = watchConsole(page);
  await signIn(page, "exec@ofs.com");
  await expect(page).toHaveURL(/\/ops$/);
  await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible();
  await expect(page.locator(".live")).toHaveText("Live");
  await expect(page.getByText("45 of 45 jobs")).toBeVisible();
  await expect(page.locator(".tile")).toHaveCount(11);
  await expect(page.locator(".ag-row")).not.toHaveCount(0);
  await page.locator(".tile", { hasText: "Ready for dispatch" }).click();
  await expect(page.getByText(/of 45 jobs, Ready for dispatch/)).toBeVisible();
  await page.getByRole("button", { name: "Clear Filter" }).click();
  await expect(page.getByText("45 of 45 jobs")).toBeVisible();
  expect(errors, errors.join("\n")).toEqual([]); // no CSP violation, no runtime error
});

test("a change made by dispatch reaches the open overview within a second", async ({ page, playwright, baseURL }) => {
  await page.setViewportSize({ width: 1440, height: 2200 }); // the grid draws only rows in view: show all 45
  await signIn(page, "exec@ofs.com");
  await expect(page.locator(".live")).toHaveText("Live");
  const assignedTile = page.locator(".tile", { hasText: /^\d+Assigned/ }).locator(".count");
  const before = Number(await assignedTile.textContent());

  const dispatch = await playwright.request.newContext({ baseURL: baseURL ?? "", extraHTTPHeaders: { Origin: baseURL ?? "" } });
  await apiAs(dispatch, "dispatch@ofs.com");
  const ready = (await (await dispatch.get("/api/jobs?state=ready_for_dispatch")).json()) as { id: string; number: number; last_event_id: number }[];
  const job = ready[0];
  if (!job) throw new Error("the seed has no ready job");
  const row = page.locator(".ag-row", { has: page.locator(`[col-id="number"]`, { hasText: String(job.number) }) });
  await expect(row.locator('[col-id="state"]')).toHaveText("Ready for dispatch");

  const started = Date.now();
  const r = await dispatch.post(`/api/jobs/${job.id}/commands`, {
    data: { command: "assign_tech", expected_event_id: job.last_event_id, payload: { tech: "Tech 1" }, override_reason: "e2e" },
  });
  expect(r.ok(), await r.text()).toBeTruthy();
  await expect(row.locator('[col-id="state"]')).toHaveText("Assigned", { timeout: 1000 });
  expect(Date.now() - started).toBeLessThan(1000);
  await expect(assignedTile).toHaveText(String(before + 1));
  await dispatch.dispose();
});

test("a tech is kept to their own view", async ({ page }) => {
  await signIn(page, "tech@ofs.com");
  await expect(page).toHaveURL(/\/ops\/tech$/);
  await page.goto("/ops");
  await expect(page).toHaveURL(/\/ops\/tech$/);
});

test("signing out ends the session", async ({ page }) => {
  await signIn(page, "controller@ofs.com");
  await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible();
  await page.getByRole("button", { name: "Sign Out" }).click();
  await expect(page).toHaveURL(/\/login$/);
  await page.goto("/ops");
  await expect(page).toHaveURL(/\/login$/);
});
