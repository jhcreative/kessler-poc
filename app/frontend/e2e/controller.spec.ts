// POC-10 in a real browser: N3 (plan §11). A closed job lands in the controller's queue with a drafted invoice;
// approving posts it to QuickBooks (simulated) and the aging moves (B1 to B3). A failed check can't be approved.
import { expect, test, type APIRequestContext, type Page, type PlaywrightWorkerArgs } from "@playwright/test";
import { makeReadyJob, office, signIn, watchConsole } from "./helpers";

type J = { id: string; number: number; last_event_id: number; state: string };


async function step(ctx: APIRequestContext, id: string, command: string, payload: object = {}, override?: string) {
  const job = (await (await ctx.get(`/api/jobs/${id}`)).json()) as J;
  const r = await ctx.post(`/api/jobs/${id}/commands`, {
    data: { command, expected_event_id: job.last_event_id, payload, override_reason: override ?? null },
  });
  expect(r.ok(), await r.text()).toBeTruthy();
}

/** Dispatch assigns a ready job to Tech 1, who arrives and closes it. */
async function workAJob(playwright: PlaywrightWorkerArgs["playwright"], baseURL: string, close: object): Promise<J> {
  const job = (await makeReadyJob(playwright, baseURL)) as unknown as J;
  const dispatch = await office(playwright, baseURL, "dispatch@kfs.com");
  await step(dispatch, job.id, "assign_tech", { tech: "Tech 1" }, "e2e");
  const tech = await office(playwright, baseURL, "tech@kfs.com");
  await step(tech, job.id, "arrive");
  await step(tech, job.id, "close_job", close);
  return job;
}

async function openJob(page: Page, number: number) {
  await page.locator(".ag-row", { has: page.locator('[col-id="number"]', { hasText: String(number) }) }).click();
}

test("a closed job arrives with its invoice; approval posts it to QuickBooks and the aging moves", async ({ page, playwright, baseURL }) => {
  await page.setViewportSize({ width: 1600, height: 1200 });
  const errors = watchConsole(page);
  await signIn(page, "controller@kfs.com");
  await expect(page).toHaveURL(/\/ops\/controller$/);
  await expect(page.locator(".live")).toHaveText("Live");
  const reviewTab = page.getByRole("tab", { name: /^Billing review/ });
  await expect(reviewTab.locator(".tab-count")).toHaveText(/^\d+$/);
  const before = Number(await reviewTab.locator(".tab-count").textContent());
  const current = page.locator(".aging .tile", { hasText: "Current" }).locator(".wait");
  await expect(current).toHaveText(/^\d+ invoices?$/);
  const currentBefore = Number((await current.textContent())?.split(" ")[0]);

  // B1: the field closes it; it lands here within a second.
  const job = await workAJob(playwright, baseURL ?? "", { actual_hours: 3, sign_off_by: "Store manager" });
  await expect(reviewTab.locator(".tab-count")).toHaveText(String(before + 1), { timeout: 1000 });

  // B2: the drafted invoice, checked; approve, and it's in QuickBooks (simulated).
  await openJob(page, job.number);
  const record = page.locator(".record");
  await expect(record.locator(".check-line").first()).toContainText("Passed the check");
  await expect(record.locator(".lines tbody tr")).toHaveCount(2);
  await record.getByRole("button", { name: "Approve and submit" }).click();
  await expect(page.locator(".toast")).toContainText(/Submitted to QuickBooks \(simulated\) as QB-\d+/);
  await expect(record.locator(".state-pill")).toHaveText("Invoiced");
  await expect(record.getByText(/Submitted to QuickBooks \(simulated\) as QB-\d+\./)).toBeVisible();

  // B3: the aging moves with it.
  await expect(current).toHaveText(`${currentBefore + 1} invoices`, { timeout: 2000 });
  expect(errors, errors.join("\n")).toEqual([]);
});

test("an invoice that failed its check can't be approved: it goes back, and the coordinator redrafts it", async ({ page, playwright, baseURL }) => {
  await page.setViewportSize({ width: 1600, height: 1200 });
  await signIn(page, "controller@kfs.com");
  await expect(page.locator(".live")).toHaveText("Live");
  const job = await workAJob(playwright, baseURL ?? "", { actual_hours: 2, no_sign_off_reason: "Store manager not on site" });
  await openJob(page, job.number);
  const record = page.locator(".record");
  await expect(record.locator(".rule-line")).toContainText("Failed the check: No sign-off from the site");
  await expect(record.getByRole("button", { name: "Approve and submit" })).toBeDisabled();
  await record.getByRole("button", { name: "Send back" }).click();
  await record.getByLabel("Why it goes back").fill("Get the sign-off from the store");
  await record.locator("form").getByRole("button", { name: "Send back" }).click();
  await expect(record.locator(".state-pill")).toHaveText("Closed");

  const coord = await office(playwright, baseURL ?? "", "coord@kfs.com");
  await step(coord, job.id, "draft_invoice");
  await expect(record.locator(".state-pill")).toHaveText("Billing review", { timeout: 1000 });
});
