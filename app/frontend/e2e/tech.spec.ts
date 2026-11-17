// POC-09 in a real browser, at phone size: N2's field half (plan §11). T1: a job dispatch assigns lands on the
// phone. T2: arrive, update the record, sign off, close. T3: needs review from the field shows at once in dispatch.
import { expect, test, type Browser, type PlaywrightWorkerArgs } from "@playwright/test";
import { makeReadyJob, office, signIn, watchConsole } from "./helpers";

test.use({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 1 });

type J = { id: string; number: number; last_event_id: number; state: string; sign_off: { by: string } | null; part_numbers: string[] };


/** A fresh ready job (the coordinator's), assigned to Tech 1 by dispatch. */
async function assignReadyToTech1(playwright: PlaywrightWorkerArgs["playwright"], baseURL: string): Promise<J> {
  const job = (await makeReadyJob(playwright, baseURL)) as unknown as J;
  const dispatch = await office(playwright, baseURL, "dispatch@kfs.com");
  const r = await dispatch.post(`/api/jobs/${job.id}/commands`, {
    data: { command: "assign_tech", expected_event_id: job.last_event_id, payload: { tech: "Tech 1" }, override_reason: "e2e" },
  });
  expect(r.ok(), await r.text()).toBeTruthy();
  return job;
}

test("a job dispatch assigns lands on the phone, and the tech works it through to billing", async ({ page, playwright, baseURL }) => {
  const errors = watchConsole(page);
  await signIn(page, "tech@kfs.com");
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
  const coord = await office(playwright, baseURL ?? "", "coord@kfs.com");
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

  await signIn(page, "tech@kfs.com");
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

test("once the client's approval is on record, the phone stops telling the tech to send it for review", async ({ page, playwright, baseURL }) => {
  // A seeded job over its client's cap: the client approves it, and dispatch sends it to Tech 1.
  const base = baseURL ?? "";
  const coord = await office(playwright, base, "coord@kfs.com");
  const [waiting] = (await (await coord.get("/api/jobs?state=needs_client_approval")).json()) as J[];
  if (!waiting) throw new Error("the seed holds no job waiting on the client");
  const step = async (who: string, command: string, payload: object = {}) => {
    const now = (await (await coord.get(`/api/jobs/${waiting.id}`)).json()) as J;
    const ctx = await office(playwright, base, who);
    const r = await ctx.post(`/api/jobs/${waiting.id}/commands`, {
      data: { command, expected_event_id: now.last_event_id, payload, override_reason: "e2e" },
    });
    expect(r.ok(), await r.text()).toBeTruthy();
  };
  await step("coord@kfs.com", "record_client_approval", { by: "Client facilities manager", client_ref: "APR-7731" });
  await step("coord@kfs.com", "approve_for_dispatch");
  await step("dispatch@kfs.com", "assign_tech", { tech: "Tech 1" });

  // And one of Tech 1's jobs under a cap, with no approval: the cap's hint still stands there.
  const tech = await office(playwright, base, "tech@kfs.com");
  type Mine = J & { approval: { client_ref: string } | null };
  const mine = ((await (await tech.get("/api/jobs?state=assigned")).json()) as Mine[]).filter((j) => !j.approval);
  let capped: Mine | undefined;
  for (const j of mine) {
    const c = (await (await tech.get(`/api/jobs/${j.id}/contract`)).json()) as { rules: { kind: string }[] };
    if (c.rules.some((r) => r.kind === "cap")) { capped = j; break; }
  }
  expect(capped, "Tech 1 holds a job under a cap").toBeTruthy();

  await signIn(page, "tech@kfs.com");
  const rails = page.locator(".rails");
  // The rules arrive with the contract, after the panel: wait for it, or "not shown" passes before they could show.
  const contractLoaded = () => page.waitForResponse((r) => r.url().endsWith("/contract") && r.ok());
  let loaded = contractLoaded();
  await page.locator(".job-card", { hasText: `job ${waiting.number}` }).click();
  await loaded;
  await expect(rails).toContainText("Client approved, ref APR-7731.");
  await expect(rails).not.toContainText("send it for review");
  loaded = contractLoaded();
  await page.goto(`/ops/tech/${capped!.id}`);
  await loaded;
  await expect(rails).toContainText("send it for review: the client approves first.");
  await expect(rails).not.toContainText("Client approved");
});

async function deskPage(browser: Browser, baseURL: string) {
  const context = await browser.newContext({ baseURL, viewport: { width: 1440, height: 900 } });
  const desk = await context.newPage();
  await signIn(desk, "dispatch@kfs.com");
  await expect(desk.locator(".live")).toHaveText("Live");
  return desk;
}
