// The demo video's take (D4): five signed-in views, each its own browser context with its own recording, driven on
// one timeline by beats.json. Every action reuses the e2e specs' selectors and flows (../e2e); nothing here changes
// the app. What it adds to each page is a visible cursor (an injected overlay that follows the real mouse events) and
// two sync flashes (the page inverted for half a second, before and after the story) so render.mjs can line the five
// recordings up to the frame. The log (events.json) is the data the EDL is built from.
//
// Run through take.sh, which reseeds the local stack first. Exit 3 means "retake": the drafted request's recommended
// tech isn't Tech 1 (the only tech with a demo login), or Claude didn't draft it, and the story needs both.
import { chromium, request } from "@playwright/test";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const BASE = process.env.VIDEO_BASE ?? "http://localhost:9219";
const TAKE = process.env.TAKE_DIR; // where this take's recordings and log go
if (!TAKE) throw new Error("TAKE_DIR is not set");
if (!/^http:\/\/(localhost|127\.0\.0\.1)[:/]/.test(BASE)) throw new Error("local stack only");
const DSF = 1.5; // Playwright video ignores deviceScaleFactor; the browser flag below makes the pixels real
const DESK = { width: 1200, height: 700 };
const PHONE = { width: 390, height: 844 };
const beats = JSON.parse(readFileSync(new URL("./beats.json", import.meta.url), "utf8")).beats;

// The e2e's own login mechanism (e2e/helpers.ts): read the file, send the password, print nothing.
const logins = Object.fromEntries(
  readFileSync(process.env.E2E_LOGINS ?? "", "utf8")
    .split("\n")
    .filter((l) => l.includes("="))
    .map((l) => [l.slice(0, l.indexOf("=")), l.slice(l.indexOf("=") + 1).trim()]),
);
async function session(email) {
  const ctx = await request.newContext({ baseURL: BASE, extraHTTPHeaders: { Origin: BASE } });
  const r = await ctx.post("/api/auth/login", { data: { email, password: logins[email] } });
  if (!r.ok()) throw new Error(`sign-in failed for ${email}: ${r.status()}`);
  return ctx;
}

const events = [];
const log = (type, data = {}) => {
  const e = { t: Date.now(), type, ...data };
  events.push(e);
  console.log(`${new Date(e.t).toISOString().slice(11, 23)} ${type}${data.id ? " " + data.id : ""}`);
  return e;
};

// The cursor: a ring that follows the mouse events Playwright sends, so a viewer sees where each click lands.
// Set through the CSSOM (allowed under the app's CSP), never as markup.
const CURSOR = () => {
  const make = () => {
    if (document.getElementById("__video_cursor")) return;
    const d = document.createElement("div");
    d.id = "__video_cursor";
    Object.assign(d.style, {
      position: "fixed", left: "-60px", top: "-60px", width: "26px", height: "26px", marginLeft: "-13px", marginTop: "-13px",
      borderRadius: "50%", background: "rgba(247,148,30,0.30)", border: "3px solid #F7941E", zIndex: "2147483647",
      pointerEvents: "none", transition: "transform 120ms ease-out, opacity 400ms", boxSizing: "border-box",
    });
    document.documentElement.appendChild(d);
    // The ring fades once the hand is still, so an idle view doesn't keep a stale mark.
    let idle;
    addEventListener("mousemove", (e) => {
      d.style.left = e.clientX + "px"; d.style.top = e.clientY + "px"; d.style.opacity = "1";
      clearTimeout(idle); idle = setTimeout(() => { d.style.opacity = "0"; }, 2500);
    }, true);
    addEventListener("mousedown", () => { d.style.transform = "scale(0.65)"; }, true);
    addEventListener("mouseup", () => { d.style.transform = "scale(1)"; }, true);
  };
  if (document.readyState === "loading") addEventListener("DOMContentLoaded", make);
  else make();
};

const browser = await chromium.launch({ args: [`--force-device-scale-factor=${DSF}`] });
const rawDir = join(TAKE, "raw");
mkdirSync(rawDir, { recursive: true });

const VIEWS = {
  coord: { email: "coord@kfs.com", path: "/ops/coordinator", phone: false },
  dispatch: { email: "dispatch@kfs.com", path: "/ops/dispatch", phone: false },
  controller: { email: "controller@kfs.com", path: "/ops/controller", phone: false },
  overview: { email: "exec@kfs.com", path: "/ops", phone: false },
  tech: { email: "tech@kfs.com", path: "/ops/tech", phone: true },
};
const pages = {};
const contexts = {};
const apis = {};

// Sign in outside the recordings (no login screen on camera), then open each recorded view with that session.
for (const [name, v] of Object.entries(VIEWS)) {
  apis[name] = await session(v.email);
  const storageState = await apis[name].storageState();
  const vp = v.phone ? PHONE : DESK;
  const size = { width: Math.round(vp.width * DSF), height: Math.round(vp.height * DSF) };
  contexts[name] = await browser.newContext({
    storageState, viewport: vp, deviceScaleFactor: DSF, recordVideo: { dir: rawDir, size },
    ...(v.phone ? { isMobile: true, hasTouch: true } : {}),
  });
  await contexts[name].addInitScript(CURSOR);
  log("page-open", { view: name });
  pages[name] = await contexts[name].newPage();
}
await Promise.all(
  Object.entries(VIEWS).map(async ([name, v]) => {
    await pages[name].goto(BASE + v.path);
    await pages[name].locator(".live").filter({ hasText: "Live" }).waitFor({ timeout: 15_000 });
  }),
);
await pages.overview.locator(".tile .count").first().waitFor();
const coordP = pages.coord, dispP = pages.dispatch, ctrlP = pages.controller, ovP = pages.overview, techP = pages.tech;
await ctrlP.locator(".aging .tile").first().waitFor();
await dispP.locator(".tab-count").first().waitFor();
await coordP.waitForTimeout(1500);

async function flash(label) {
  log("flash", { id: label });
  await Promise.all(
    Object.values(pages).map((p) =>
      p.evaluate(() => {
        document.documentElement.style.filter = "invert(1)";
        setTimeout(() => { document.documentElement.style.filter = ""; }, 500);
      }),
    ),
  );
  await coordP.waitForTimeout(1500);
}
await flash("start");

// One beat: log its start, run its actions, then hold until its minimum time has passed (reading time).
const byId = Object.fromEntries(beats.map((b) => [b.id, b]));
async function beat(id, actions) {
  if (!byId[id]) throw new Error(`no beat ${id}`);
  const start = log("beat", { id });
  await actions();
  const left = byId[id].min_ms - (Date.now() - start.t);
  if (left > 0) await coordP.waitForTimeout(left);
}

// Move the cursor to an element, smoothly, then click it.
async function press(page, locator, { click = true } = {}) {
  await locator.scrollIntoViewIfNeeded();
  const b = await locator.boundingBox();
  if (!b) throw new Error("nothing to press");
  const x = b.x + b.width / 2, y = b.y + b.height / 2;
  await page.mouse.move(x, y, { steps: 18 });
  await page.waitForTimeout(280);
  if (click) await page.mouse.click(x, y);
}
async function type(page, locator, text) {
  await press(page, locator);
  await locator.fill("");
  await locator.pressSequentially(text, { delay: 90 });
}
const recordTop = async (page) => page.locator(".record h2").first().scrollIntoViewIfNeeded().catch(() => {});

let number = "";
let exit = 0;
try {
  await beat("establish", async () => {
    await press(coordP, coordP.getByRole("button", { name: "New request" }), { click: false });
  });

  // N1: a request arrives and is drafted (coordinator.spec.ts).
  await beat("new-request", async () => {
    await press(coordP, coordP.getByRole("button", { name: "New request" }));
    await coordP.locator(".toast").filter({ hasText: /New request from .+, drafted by (Claude|the rules)/ }).waitFor({ timeout: 45_000 });
    await coordP.locator(".record .state-pill").filter({ hasText: "Intake draft" }).waitFor();
  });
  const record = coordP.locator(".record");
  number = (await record.locator("h2").textContent())?.match(/Job (\d+)/)?.[1] ?? "";
  const drafted = (await record.locator(".drafted").textContent()) ?? "";
  const job = ((await (await apis.coord.get("/api/jobs?state=intake_draft")).json())).find((j) => String(j.number) === number);
  const rec = await (await apis.dispatch.get(`/api/jobs/${job.id}/recommendation`)).json();
  log("drafted", { number, by: /Claude/.test(drafted) ? "Claude" : "rules", top: rec.top?.label ?? null, issue: job.issue_type });
  if (!/Drafted by Claude/.test(drafted) || rec.top?.label !== "Tech 1") {
    exit = 3;
    throw new Error(`retake: drafted by ${/Claude/.test(drafted) ? "Claude" : "the rules"}, recommended ${rec.top?.label}`);
  }

  await beat("draft", async () => {
    await coordP.waitForTimeout(1200);
    await press(coordP, record.getByText("The request as it arrived"));
    await record.locator(".source pre").waitFor();
    await coordP.waitForTimeout(400);
    await record.locator(".source pre").scrollIntoViewIfNeeded();
  });

  await beat("draft-lands", async () => {
    await recordTop(coordP);
    await press(ovP, ovP.locator(".tile", { hasText: "Intake draft" }), { click: false });
  });

  await beat("qualify", async () => {
    await press(coordP, record.getByRole("button", { name: "Qualify" }));
    await record.locator(".state-pill").filter({ hasText: "Qualified" }).waitFor();
  });

  // N1b: over the cap, the rule holds dispatch (coordinator.spec.ts).
  await beat("estimate", async () => {
    await type(coordP, record.getByRole("textbox", { name: /^Estimate \(/ }), "49000");
    await coordP.waitForTimeout(500);
    await press(coordP, record.getByRole("button", { name: "Save" }));
    await coordP.locator(".toast").filter({ hasText: `Saved job ${number}` }).waitFor();
  });

  await beat("rule", async () => {
    await record.locator(".rule-line").filter({ hasText: "needs the client's approval first" }).waitFor();
    await record.locator(".rule-line").first().scrollIntoViewIfNeeded();
    await press(coordP, record.getByRole("button", { name: "Approve for dispatch" }), { click: false });
  });

  await beat("approval", async () => {
    await press(coordP, record.getByRole("button", { name: "Request client approval" }));
    await record.locator(".state-pill").filter({ hasText: "Needs client approval" }).waitFor();
    await coordP.waitForTimeout(900);
    await type(coordP, record.getByLabel("Client reference"), "APR-7731");
    await coordP.waitForTimeout(400);
    await press(coordP, record.getByRole("button", { name: "Record approval" }));
    await record.locator(".state-pill").filter({ hasText: "Qualified" }).waitFor();
    await record.getByText(/ref APR-7731/).waitFor();
  });

  // D1: approved, it lands in Ready (dispatch.spec.ts).
  const readyTab = dispP.getByRole("tab", { name: /^Ready/ });
  await beat("to-dispatch", async () => {
    await press(coordP, record.getByRole("button", { name: "Approve for dispatch" }));
    await record.locator(".state-pill").filter({ hasText: "Ready for dispatch" }).waitFor();
    await recordTop(coordP);
    await press(dispP, readyTab, { click: false });
  });

  // D2: the recommendation and its reasons.
  const drec = dispP.locator(".record");
  await beat("recommend", async () => {
    await press(dispP, dispP.locator(".ag-row", { has: dispP.locator('[col-id="number"]', { hasText: number }) }));
    await drec.locator(".recommended").filter({ hasText: "Recommended:" }).waitFor();
    await press(dispP, drec.locator(".recommended"), { click: false });
  });

  // D3 and T1: one click, and the phone has it (dispatch.spec.ts, tech.spec.ts).
  const card = techP.locator(".job-card", { hasText: `job ${number}` });
  await beat("assign", async () => {
    await press(dispP, drec.getByRole("button", { name: "Assign Tech 1" }));
    await drec.locator(".state-pill").filter({ hasText: "Assigned" }).waitFor();
    await card.waitFor({ timeout: 2000 });
    await record.locator(".state-pill").filter({ hasText: "Assigned" }).waitFor({ timeout: 2000 });
  });

  // T2: arrive, close with a sign-off (tech.spec.ts).
  await beat("phone-open", async () => {
    await press(techP, card);
    await techP.getByRole("heading", { name: `Job ${number}` }).waitFor();
  });

  await beat("arrive", async () => {
    await press(techP, techP.getByRole("button", { name: "Arrive" }));
    await techP.locator(".job-head .state-pill").filter({ hasText: "Onsite" }).waitFor();
  });

  const billingTab = ctrlP.getByRole("tab", { name: /^Billing review/ });
  await beat("close", async () => {
    await press(techP, techP.getByRole("button", { name: "Close job" }));
    await techP.waitForTimeout(600);
    await type(techP, techP.getByLabel("Hours on site").last(), "2.5");
    await techP.waitForTimeout(600);
    await press(techP, techP.getByRole("button", { name: "Close and send to billing" }));
    await techP.waitForURL(/\/ops\/tech$/);
  });

  // B1: the field closed it; it's in billing with its invoice (controller.spec.ts).
  const crec = ctrlP.locator(".record");
  await beat("to-billing", async () => {
    await press(ctrlP, billingTab, { click: false });
    await ctrlP.waitForTimeout(1500);
    await press(ctrlP, ctrlP.locator(".ag-row", { has: ctrlP.locator('[col-id="number"]', { hasText: number }) }));
    await crec.locator(".check-line").first().waitFor();
  });

  await beat("invoice", async () => {
    await press(ctrlP, crec.locator(".check-line").first(), { click: false });
  });

  const current = ctrlP.locator(".aging .tile", { hasText: "Current" }).locator(".wait");
  const currentBefore = Number((await current.textContent())?.split(" ")[0]);
  await beat("submit", async () => {
    await press(ctrlP, crec.getByRole("button", { name: "Approve and submit" }));
    await ctrlP.locator(".toast").filter({ hasText: /Submitted to QuickBooks \(simulated\) as QB-\d+/ }).waitFor();
    await crec.locator(".state-pill").filter({ hasText: "Invoiced" }).waitFor();
  });

  await beat("aging", async () => {
    await current.filter({ hasText: `${currentBefore + 1} invoice` }).waitFor({ timeout: 3000 });
    await press(ctrlP, ctrlP.locator(".aging .tile", { hasText: "Current" }), { click: false });
  });

  // N4: the overview (overview.spec.ts).
  await beat("overview", async () => {
    await press(ovP, ovP.locator(".tile", { hasText: "Billing review" }), { click: false });
    await ovP.waitForTimeout(2500);
    await press(ovP, ovP.locator(".tile", { hasText: "Needs client approval" }), { click: false });
  });

  await beat("overview-filter", async () => {
    await press(ovP, ovP.locator(".tile", { hasText: /^\d+Invoiced/ }));
    await ovP.locator(".showing").filter({ hasText: "Invoiced" }).waitFor();
    const row = ovP.locator(".ag-row", { has: ovP.locator('[col-id="number"]', { hasText: number }) });
    await row.waitFor();
    await press(ovP, row, { click: false });
  });

  await beat("history", async () => {
    await press(coordP, record.locator(".history"), { click: false });
    await record.locator(".history li").first().waitFor();
  });
  log("story-end");
  await flash("end");
} catch (e) {
  log("error", { message: String(e.message ?? e).split("\n")[0] });
  if (!exit) exit = 1;
}

// Close each context (that finishes its video), then copy it out under the view's name at once.
const videos = {};
for (const [name, ctx] of Object.entries(contexts)) {
  const v = pages[name].video();
  await ctx.close();
  if (v && exit === 0) {
    const dest = join(TAKE, `${name}.webm`);
    await v.saveAs(dest);
    videos[name] = `${name}.webm`;
  }
}
await browser.close();
for (const a of Object.values(apis)) await a.dispose();
writeFileSync(join(TAKE, "events.json"), JSON.stringify({ base: BASE, dsf: DSF, desk: DESK, phone: PHONE, number, videos, events }, null, 2));
process.exit(exit);
