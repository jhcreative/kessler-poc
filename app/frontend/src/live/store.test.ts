import { describe, expect, it } from "vitest";
import type { Job, LiveEvent } from "../api/types";
import { apply, empty, load, newestFirst } from "./store";

const job = (id: string, last: number, over: Partial<Job> = {}): Job =>
  ({ id, number: 1000 + last, last_event_id: last, state: "qualified", updated_at: `2026-11-16T09:${String(last).padStart(2, "0")}:00Z`, tech_id: null, ...over }) as Job;

const msg = (j: Job, eventId = j.last_event_id): LiveEvent =>
  ({ type: "event", event: { id: eventId, job_id: j.id }, job: j }) as LiveEvent;

describe("the live store", () => {
  it("loads, and replays after the highest event it holds", () => {
    const s = load([job("a", 3), job("b", 7)]);
    expect(s.lastEventId).toBe(7);
    expect(s.jobs.size).toBe(2);
  });

  it("moves a job forward and flashes it once", () => {
    const s = apply(load([job("a", 3)]), msg(job("a", 9, { state: "ready_for_dispatch" })));
    expect(s.jobs.get("a")?.state).toBe("ready_for_dispatch");
    expect(s.flashed.get("a")).toBe(9);
    expect(s.lastEventId).toBe(9);
  });

  it("never moves a job back: an older or repeated frame changes nothing", () => {
    const s = apply(load([job("a", 9, { state: "assigned" })]), msg(job("a", 5, { state: "qualified" })));
    expect(s.jobs.get("a")?.state).toBe("assigned");
    const again = apply(s, msg(job("a", 9, { state: "assigned" })));
    expect(again).toBe(s);
  });

  it("adds a job it hadn't seen, and drops one that leaves this view's scope", () => {
    const mine = (j: Job) => j.tech_id === "t1";
    let s = apply(empty, msg(job("a", 4, { tech_id: "t1" })), { inScope: mine });
    expect(s.jobs.has("a")).toBe(true);
    s = apply(s, msg(job("a", 6, { tech_id: "t2" })), { inScope: mine });
    expect(s.jobs.has("a")).toBe(false);
  });

  it("applies frames buffered before the list arrived, without flashing", () => {
    const s = load([job("a", 3)], [msg(job("a", 4, { state: "ready_for_dispatch" }))]);
    expect(s.jobs.get("a")?.state).toBe("ready_for_dispatch");
    expect(s.flashed.size).toBe(0);
  });

  it("keeps buffered frames to the view's scope", () => {
    const mine = (j: Job) => j.tech_id === "t1";
    const s = load([job("a", 3, { tech_id: "t1" })], [msg(job("a", 4, { tech_id: "t2" }))], mine);
    expect(s.jobs.has("a")).toBe(false);
  });

  it("lists newest first", () => {
    expect(newestFirst(load([job("a", 1), job("b", 5)]).jobs).map((j) => j.id)).toEqual(["b", "a"]);
  });
});
