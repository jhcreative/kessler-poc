// POC-08 in a real browser: N2's dispatch half (plan §11). D1: an approved job arrives live. D2: it shows the
// recommended tech and why. D3: one click assigns it. Then the soft rail (a reason on record) and T4.
import { expect, test, type APIRequestContext } from "@playwright/test";
import { apiAs, office, signIn, watchConsole } from "./helpers";

type J = { id: string; number: number; last_event_id: number; requires_approval: boolean; state: string };

async function command(ctx: APIRequestContext, job: J, command: string, payload = {}) {
  const fresh = (await (await ctx.get(`/api/jobs/${job.id}`)).json()) as J;
  const r = await ctx.post(`/api/jobs/${job.id}/commands`, { data: { command, expected_event_id: fresh.last_event_id, payload } });
  expect(r.ok(), await r.text()).toBeTruthy();
}

test("an approved job arrives in dispatch with its recommended tech, and one click assigns it", async ({ page, playwright, baseURL }) => {
  await page.setViewportSize({ width: 1600, height: 1400 });
  const errors = watchConsole(page);
  await signIn(page, "dispatch@kfs.com");
  await expect(page).toHaveURL(/\/ops\/dispatch$/);
  await expect(page.locator(".live")).toHaveText("Live");
  const readyTab = page.getByRole("tab", { name: /^Ready/ });
  await expect(readyTab.locator(".tab-count")).toHaveText(/^\d+$/); // the list has loaded: read the real count
  const before = Number(await readyTab.locator(".tab-count").textContent());

  // D1: the coordinator approves a draft elsewhere; it lands in Ready.
  const coord = await office(playwright, baseURL ?? "", "coord@kfs.com");
  const drafts = (await (await coord.get("/api/jobs?state=intake_draft")).json()) as J[];
  const job = drafts.find((j) => !j.requires_approval);
  if (!job) throw new Error("no draft without a rule");
  await command(coord, job, "qualify");
  await command(coord, job, "approve_for_dispatch");
  await expect(readyTab.locator(".tab-count")).toHaveText(String(before + 1), { timeout: 1000 });

  // D2: open it; the recommendation says who and why.
  await page.locator(".ag-row", { has: page.locator('[col-id="number"]', { hasText: String(job.number) }) }).click();
  const record = page.locator(".record");
  await expect(record.locator(".recommended")).toContainText("Recommended:");
  await expect(record.locator(".recommended li")).toHaveCount(4);
  await expect(record.locator(".recommended")).toContainText(/Licensed in [A-Z]{2}/);
  const name = (await record.locator(".recommended-name strong").textContent()) ?? "";

  // D3: assign; the job leaves Ready and shows its tech.
  await record.getByRole("button", { name: `Assign ${name}` }).click();
  await expect(page.locator(".toast")).toContainText(`Assigned a tech to ${name}: job ${job.number}`);
  await expect(record.locator(".state-pill")).toHaveText("Assigned");
  await expect(readyTab.locator(".tab-count")).toHaveText(String(before));
  expect(errors, errors.join("\n")).toEqual([]);
});

test("a tech who doesn't qualify takes a reason, and the reason goes on record", async ({ page, request }) => {
  await page.setViewportSize({ width: 1600, height: 1400 });
  await signIn(page, "dispatch@kfs.com");
  await page.locator(".queue-grid .ag-row").first().click();
  const record = page.locator(".record");
  const misfit = record.locator(".candidate:not([data-eligible])").first();
  const name = (await misfit.locator(".candidate-name").textContent()) ?? "";
  await misfit.getByRole("button", { name: "Assign" }).click();
  await misfit.getByLabel(`Why assign ${name}`).fill("The licensed techs are all out today");
  await misfit.getByRole("button", { name: "Assign anyway" }).click();
  await expect(record.locator(".state-pill")).toHaveText("Assigned");
  const number = (await record.locator("h2").textContent())?.match(/Job (\d+)/)?.[1];
  await apiAs(request, "dispatch@kfs.com");
  const jobs = (await (await request.get("/api/jobs?state=assigned")).json()) as J[];
  const job = jobs.find((j) => String(j.number) === number);
  const events = (await (await request.get(`/api/jobs/${job?.id}/events`)).json()) as { command: string; override_reason: string | null }[];
  expect(events.at(-1)).toMatchObject({ command: "assign_tech", override_reason: "The licensed techs are all out today" });
});

test("needs review: dispatch asks the tech to wait, and the job goes back to work", async ({ page }) => {
  await page.setViewportSize({ width: 1600, height: 1400 });
  await signIn(page, "dispatch@kfs.com");
  await page.getByRole("tab", { name: /^Needs review/ }).click();
  await page.locator(".queue-grid .ag-row").first().click();
  const record = page.locator(".record");
  await expect(record.locator(".state-pill")).toHaveText("Needs review");
  await expect(record.getByText("Why review")).toBeVisible();
  await record.getByRole("button", { name: "Ask tech to wait" }).click();
  await expect(record.locator(".state-pill")).toHaveText("Onsite");
});
