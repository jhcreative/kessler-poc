// POC-09 in a real browser, at phone size: N2's field half (plan §11). T1: a job dispatch assigns lands on the
// phone. T2: arrive, update the record, sign off, close. T3: needs review from the field shows at once in dispatch.
import { expect, test, type Browser, type PlaywrightWorkerArgs } from "@playwright/test";
import { makeReadyJob, office, signIn, watchConsole } from "./helpers";

test.use({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 1 });

type J = { id: string; number: number; last_event_id: number; state: string; sign_off: { by: string } | null; part_numbers: string[] };


/** A fresh ready job (the coordinator's), assigned to Tech 1 by dispatch. */
async function assignReadyToTech1(playwright: PlaywrightWorkerArgs["playwright"], baseURL: string): Promise<J> {
  const job = (await makeReadyJob(playwright, baseURL)) as unknown as J;
  const dispatch = await office(playwright, baseURL, "dispatch@ofs.com");
  const r = await dispatch.post(`/api/jobs/${job.id}/commands`, {
    data: { command: "assign_tech", expected_event_id: job.last_event_id, payload: { tech: "Tech 1" }, override_reason: "e2e" },
  });
  expect(r.ok(), await r.text()).toBeTruthy();
  return job;
}

test("a job dispatch assigns lands on the phone, and the tech works it through to billing", async ({ page, playwright, baseURL }) => {
  const errors = watchConsole(page);
  await signIn(page, "tech@ofs.com");
  await expect(page).toHaveURL(/\/ops\/tech$/);
  await expect(page.locator(".live")).toHaveText("Live");
  // T1: assigned elsewhere, on the schedule within a second.
  const job = await assignReadyToTech1(playwright, baseURL ?? "");
  const card = page.locator(".job-card", { hasText: `job ${job.number}` });
  await expect(card).toBeVisible({ timeout: 1000 });
  await expect(card.locator(".state-pill")).toHaveText("Assigned");

  // T2: arrive, record the parts, close with a sign-off.
  await card.click();
  await expect(page.getByRole("heading", { name: `Job ${job.number}` })).toBeVisible();
  await expect(page.getByText("The site signs off, or you say why they can't.")).toBeVisible();
  await page.getByRole("button", { name: "Arrive" }).click();
  await expect(page.locator(".job-head .state-pill")).toHaveText("Onsite");
  await page.getByLabel("Parts", { exact: true }).selectOption("special_order");
  await page.getByLabel("Part numbers").fill("PN-48213");
  await page.getByRole("button", { name: "Save" }).click();
  await expect(page.locator(".toast")).toContainText(`Updated fields: job ${job.number}`);
  await page.getByRole("button", { name: "Close job" }).click();
  await page.getByLabel("Hours on site").last().fill("2.5");
  await page.getByRole("button", { name: "Close and send to billing" }).click();
  await expect(page).toHaveURL(/\/ops\/tech$/);
  await expect(page.locator(".job-card", { hasText: `job ${job.number}` })).toHaveCount(0);

  // The one record: the office sees what the field wrote.
  const coord = await office(playwright, baseURL ?? "", "coord@ofs.com");
  const after = (await (await coord.get(`/api/jobs/${job.id}`)).json()) as J;
  expect(after.state).toBe("billing_review"); // closed, and the invoice drafted at close
  expect(after.sign_off?.by).toBe("Store manager");
  expect(after.part_numbers).toEqual(["PN-48213"]);
  expect(errors, errors.join("\n")).toEqual([]);
});

test("needs review from the field shows in dispatch at once", async ({ page, playwright, baseURL, browser }) => {
  const job = await assignReadyToTech1(playwright, baseURL ?? "");

  // Dispatch, on a desk, watching Needs review.
  const desk = await deskPage(browser, baseURL ?? "");
  const reviewTab = desk.getByRole("tab", { name: /^Needs review/ });
  await expect(reviewTab.locator(".tab-count")).toHaveText(/^\d+$/);
  const before = Number(await reviewTab.locator(".tab-count").textContent());

  await signIn(page, "tech@ofs.com");
  await page.locator(".job-card", { hasText: `job ${job.number}` }).click();
  await page.getByRole("button", { name: "Arrive" }).click();
  await expect(page.locator(".job-head .state-pill")).toHaveText("Onsite");
  await page.getByRole("button", { name: "Needs review" }).click();
  await page.getByLabel("Why").selectOption("parts_delay");
  await page.getByLabel("One line for dispatch").fill("Compressor is on backorder");
  await page.getByRole("button", { name: "Send for review" }).click();
  await expect(page.locator(".job-head .state-pill")).toHaveText("Needs review");
  await expect(page.locator(".rule-line")).toContainText("Waiting on dispatch (Parts delay: Compressor is on backorder)");
  await expect(reviewTab.locator(".tab-count")).toHaveText(String(before + 1), { timeout: 1000 }); // T3
  await desk.context().close();
});

async function deskPage(browser: Browser, baseURL: string) {
  const context = await browser.newContext({ baseURL, viewport: { width: 1440, height: 900 } });
  const desk = await context.newPage();
  await signIn(desk, "dispatch@ofs.com");
  await expect(desk.locator(".live")).toHaveText("Live");
  return desk;
}
