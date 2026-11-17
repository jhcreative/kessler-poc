// POC-07 in a real browser: N1 and N1b (plan §11). A request arrives and is drafted from source; the coordinator
// checks it, the contract rule holds dispatch until the client's approval is on record, and once dispatched the
// job moves on in the coordinator's open record as dispatch acts (G1, C1 to C3).
import { expect, test } from "@playwright/test";
import { apiAs, signIn, watchConsole } from "./helpers";

test("a request goes from draft to dispatch, through the approval rule, and moves on live", async ({ page, playwright, baseURL }) => {
  test.setTimeout(60_000);
  await page.setViewportSize({ width: 1600, height: 1400 });
  const errors = watchConsole(page);
  await signIn(page, "coord@kfs.com");
  await expect(page).toHaveURL(/\/ops\/coordinator$/);
  await expect(page.locator(".live")).toHaveText("Live");

  // C2: a request arrives and is drafted, by Claude or, labelled, by the rules.
  // One new request every few seconds per person: earlier tests sent some as this coordinator, so the first click
  // may be told to wait, as a person would be. Then try again.
  await page.getByRole("button", { name: "New request" }).click();
  const toast = page.locator(".toast");
  await expect(toast).toContainText(/New request from|One new request every few seconds/, { timeout: 20_000 });
  if ((await toast.textContent())?.includes("every few seconds")) {
    // The wait is the answer this branch expects: the browser logs its 429, and that one line isn't an error.
    errors.splice(0, errors.length, ...errors.filter((e) => !/status of 429/.test(e)));
    await toast.getByRole("button", { name: "Dismiss" }).click();
    await page.waitForTimeout(3100);
    await page.getByRole("button", { name: "New request" }).click();
  }
  await expect(toast).toContainText(/New request from .+, drafted by (Claude|the rules)/, { timeout: 20_000 });
  const record = page.locator(".record");
  await expect(record.locator(".state-pill")).toHaveText("Intake draft");
  await expect(record.locator(".drafted")).toContainText(/Drafted by (Claude|the rules) from source/);
  await record.getByText("The request as it arrived").click();
  await expect(record.locator(".source pre")).not.toBeEmpty();
  const number = (await record.locator("h2").textContent())?.match(/Job (\d+)/)?.[1] ?? "";

  await record.getByRole("button", { name: "Qualify" }).click();
  await expect(record.locator(".state-pill")).toHaveText("Qualified");

  // C3: over the cap, the rule holds dispatch until the approval is on record.
  await record.getByRole("textbox", { name: /^Estimate \(/ }).fill("49000");
  await record.getByRole("button", { name: "Save" }).click();
  await expect(page.locator(".toast")).toContainText(`Saved job ${number}`);
  await expect(record.locator(".rule-line")).toContainText("needs the client's approval first");
  await expect(record.getByRole("button", { name: "Approve for dispatch" })).toBeDisabled();
  await record.getByRole("button", { name: "Request client approval" }).click();
  await expect(record.locator(".state-pill")).toHaveText("Needs client approval");
  await record.getByLabel("Client reference").fill("APR-7731");
  await record.getByRole("button", { name: "Record approval" }).click();
  await expect(record.locator(".state-pill")).toHaveText("Qualified");
  await expect(record.getByText(/ref APR-7731/)).toBeVisible();
  await record.getByRole("button", { name: "Approve for dispatch" }).click();
  await expect(record.locator(".state-pill")).toHaveText("Ready for dispatch");

  // N1: dispatch acts elsewhere; the coordinator's open record moves on by itself.
  const dispatch = await playwright.request.newContext({ baseURL: baseURL ?? "", extraHTTPHeaders: { Origin: baseURL ?? "" } });
  await apiAs(dispatch, "dispatch@kfs.com");
  const jobs = (await (await dispatch.get("/api/jobs?state=ready_for_dispatch")).json()) as { id: string; number: number; last_event_id: number }[];
  const job = jobs.find((j) => String(j.number) === number);
  if (!job) throw new Error(`job ${number} isn't ready for dispatch`);
  const r = await dispatch.post(`/api/jobs/${job.id}/commands`, {
    data: { command: "assign_tech", expected_event_id: job.last_event_id, payload: { tech: "Tech 1" }, override_reason: "e2e" },
  });
  expect(r.ok(), await r.text()).toBeTruthy();
  await expect(record.locator(".state-pill")).toHaveText("Assigned", { timeout: 1000 });
  await expect(record.locator(".history li").first()).toContainText("Assigned a tech by Dispatcher");
  await dispatch.dispose();
  expect(errors, errors.join("\n")).toEqual([]);
});
