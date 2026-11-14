import { expect, type APIRequestContext, type Page } from "@playwright/test";
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
