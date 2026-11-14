// The live store: every job a view can see, kept current from the WebSocket (G1).
// Pure, so it's tested without a socket. A frame only ever moves a job forward: a job snapshot older than the one
// we hold (by last_event_id) is ignored, so replay and live frames can arrive in any order and nothing goes back.
import type { Job, LiveEvent } from "../api/types";

export interface LiveState {
  jobs: ReadonlyMap<string, Job>;
  lastEventId: number; // the highest event id seen: what a reconnect asks to replay after
  flashed: ReadonlyMap<string, number>; // job id to the event id that last changed it, so a row flashes once
}

export const empty: LiveState = { jobs: new Map(), lastEventId: 0, flashed: new Map() };

export function load(jobs: readonly Job[], buffered: readonly LiveEvent[] = []): LiveState {
  const state: LiveState = {
    jobs: new Map(jobs.map((j) => [j.id, j])),
    lastEventId: Math.max(0, ...jobs.map((j) => j.last_event_id)),
    flashed: new Map(),
  };
  return buffered.reduce((s, m) => apply(s, m, { flash: false }), state);
}

export function apply(
  state: LiveState,
  msg: LiveEvent,
  opts: { flash?: boolean; inScope?: (job: Job) => boolean } = {},
): LiveState {
  const { flash = true, inScope = () => true } = opts;
  const lastEventId = Math.max(state.lastEventId, msg.event.id);
  const held = state.jobs.get(msg.job.id);
  if (held && held.last_event_id >= msg.job.last_event_id) {
    return lastEventId === state.lastEventId ? state : { ...state, lastEventId };
  }
  const jobs = new Map(state.jobs);
  if (inScope(msg.job)) jobs.set(msg.job.id, msg.job);
  else jobs.delete(msg.job.id); // e.g. a job reassigned away from this tech
  const flashed = flash ? new Map(state.flashed).set(msg.job.id, msg.event.id) : state.flashed;
  return { jobs, lastEventId, flashed };
}

export function newestFirst(jobs: ReadonlyMap<string, Job>): Job[] {
  return [...jobs.values()].sort((a, b) => b.updated_at.localeCompare(a.updated_at)); // PQ-29
}
