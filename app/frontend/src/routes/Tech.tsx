// View 2's field app (page 4; T1 to T3): the tech's phone. Hand-rolled, phone first (ADR: grids only where grids
// belong). The schedule is the tech's own jobs only (the server filters; the live store keeps it that way), and the
// job screen updates the one record, so the coordinator and dispatch see it at once.
import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router";
import { ApiError, api } from "../api/client";
import type { ContractOut, FieldsIn, Job } from "../api/types";
import { useAuth } from "../auth";
import { COMMAND_LABEL, ISSUE_LABEL, STATE_LABEL, dollars, when } from "../format";
import { useLive } from "../live/useLive";
import { useToast } from "../Toast";
import { useDelayed } from "../useDelayed";
import { ViewTitle } from "./ViewTitle";

const ACTIVE = ["onsite", "needs_review", "assigned"] as const;
const DONE = ["closed", "billing_review", "invoiced", "paid"];
type Extenuating = NonNullable<FieldsIn["extenuating"]>[number];
const REASONS: { value: Extenuating; label: string }[] = [
  { value: "parts_delay", label: "Parts delay" },
  { value: "scope_changed", label: "Scope changed" },
  { value: "access_denied", label: "Access denied" },
  { value: "safety_hold", label: "Safety hold" },
  { value: "other", label: "Other" },
];

function schedule(jobs: Iterable<Job>): Job[] {
  // Onsite first, then needs review, then assigned by window: the job in hand, then what's next (T1).
  const rank = (j: Job) => ACTIVE.indexOf(j.state as (typeof ACTIVE)[number]);
  return [...jobs]
    .filter((j) => rank(j) >= 0)
    .sort((a, b) => rank(a) - rank(b) || (a.window_start ?? "").localeCompare(b.window_start ?? ""));
}

export function Tech() {
  const { me, signedOut } = useAuth();
  const { jobId } = useParams();
  const mine = useMemo(() => (j: Job) => j.tech_id === me?.tech_id, [me?.tech_id]);
  const { state, status, loaded, error } = useLive({ onSignedOut: signedOut, inScope: mine }); // a job reassigned away leaves
  const skeleton = useDelayed(!loaded);
  const jobs = useMemo(() => schedule(state.jobs.values()), [state.jobs]);
  const done = useMemo(() => [...state.jobs.values()].filter((j) => DONE.includes(j.state)).length, [state.jobs]);
  if (me && me.role !== "tech") return <Navigate to="/ops" replace />;
  const job = jobId ? state.jobs.get(jobId) : undefined;

  if (jobId) {
    if (!loaded) return <main className="phone">{skeleton && <div className="skeleton" style={{ height: 240 }} />}</main>;
    if (!job) return <Navigate to="/ops/tech" replace />; // reassigned away, or not theirs
    return <JobScreen job={job} status={status} />;
  }

  return (
    <main className="phone" aria-busy={!loaded}>
      <ViewTitle title="My schedule" status={status} />
      {error && <p className="error-line" role="alert">{error}</p>}
      {!loaded ? (
        skeleton && [0, 1, 2].map((i) => <div key={i} className="job-card skeleton" aria-hidden="true" />)
      ) : jobs.length === 0 ? (
        <p className="status-line">Nothing on your schedule. New jobs appear here as dispatch assigns them.</p>
      ) : (
        <ol className="cards">
          {jobs.map((j) => (
            <li key={j.id}>
              <Link className="job-card" to={`/ops/tech/${j.id}`} data-state={j.state}>
                <span className="card-time">{j.window_start ? when(j.window_start) : "No window yet"}</span>
                <span className="card-title">{j.site_label}</span>
                <span className="card-line">
                  {ISSUE_LABEL[j.issue_type] ?? j.issue_type}, job {j.number}
                </span>
                <span className="state-pill">{STATE_LABEL[j.state]}</span>
              </Link>
            </li>
          ))}
        </ol>
      )}
      {loaded && done > 0 && <p className="status-line">{done} done and handed to billing.</p>}
    </main>
  );
}

function JobScreen({ job, status }: { job: Job; status: "connecting" | "live" | "reconnecting" }) {
  const toast = useToast();
  const navigate = useNavigate();
  const [contract, setContract] = useState<ContractOut | null>(null);
  const [busy, setBusy] = useState(false);
  const [panel, setPanel] = useState<"none" | "review" | "close">("none");
  useEffect(() => {
    api.contract(job.id).then(setContract).catch(() => setContract(null));
  }, [job.id]);

  const run = async (command: string, payload: Record<string, unknown> = {}) => {
    setBusy(true);
    try {
      await api.command(job.id, { command, expected_event_id: job.last_event_id, payload, override_reason: null });
      toast(`${COMMAND_LABEL[command] ?? command}: job ${job.number}`);
      setPanel("none");
      if (command === "close_job") navigate("/ops/tech"); // closed: back to what's next
    } catch (e) {
      toast(e instanceof ApiError ? e.message : "That didn't go through", true);
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="phone">
      <ViewTitle title={`Job ${job.number}`} status={status} />
      <Link className="back" to="/ops/tech">
        My schedule
      </Link>
      <section className="job-head">
        <span className="state-pill">{STATE_LABEL[job.state]}</span>
        <h2>{job.site_label}</h2>
        <p className="card-line">{job.site_address}</p>
        <p className="card-line">
          {job.site_contact}, work order {job.client_wo}
        </p>
      </section>

      <section className="rails" aria-labelledby="rails">
        <h3 id="rails">Before you close</h3>
        <ul>
          <li>The site signs off, or you say why they can't.</li>
          {job.requires_approval && <li>{job.approval ? `Client approved, ref ${job.approval.client_ref}.` : `${job.rule_fired}.`}</li>}
          {contract?.rules.map((r) =>
            r.kind === "cap" ? (
              <li key={r.text}>
                If the work will run over <span className="unit">$</span>
                {dollars(r.amount_cents)}, send it for review: the client approves first.
              </li>
            ) : null,
          )}
        </ul>
      </section>

      {job.state === "assigned" && (
        <button type="button" className="primary block" disabled={busy} onClick={() => void run("arrive")}>
          Arrive
        </button>
      )}

      {job.state === "needs_review" && (
        <p className="rule-line">Waiting on dispatch ({job.extenuating_note ?? "flagged for review"}). You'll see their decision here.</p>
      )}

      {job.state === "onsite" && (
        <>
          <PhoneFields job={job} busy={busy} onSave={(c) => void run("update_fields", c)} />
          {panel === "none" && (
            <div className="phone-actions">
              <button type="button" className="primary block" disabled={busy} onClick={() => setPanel("close")}>
                Close job
              </button>
              <button type="button" className="secondary block" disabled={busy} onClick={() => setPanel("review")}>
                Needs review
              </button>
            </div>
          )}
          {panel === "review" && <ReviewForm busy={busy} onCancel={() => setPanel("none")} onSubmit={(reason) => void run("set_needs_review", { reason })} />}
          {panel === "close" && <CloseForm job={job} busy={busy} onCancel={() => setPanel("none")} onSubmit={(p) => void run("close_job", p)} />}
        </>
      )}
    </main>
  );
}

// Part B from the field: the same typed fields the coordinator sees, two ways (plan §5). Only changes are sent.
function PhoneFields({ job, busy, onSave }: { job: Job; busy: boolean; onSave: (c: FieldsIn) => void }) {
  const initial = useMemo(
    () => ({ parts: job.parts, part_numbers: job.part_numbers.join(", "), actual_hours: job.actual_hours == null ? "" : String(job.actual_hours) }),
    [job],
  );
  const [form, setForm] = useState(initial);
  useEffect(() => setForm(initial), [initial]);
  const changes: FieldsIn = {};
  if (form.parts !== initial.parts) changes.parts = form.parts;
  if (form.part_numbers !== initial.part_numbers) changes.part_numbers = form.part_numbers.split(",").map((s) => s.trim()).filter(Boolean);
  if (form.actual_hours !== initial.actual_hours) changes.actual_hours = form.actual_hours === "" ? null : Number(form.actual_hours);
  const valid = form.actual_hours === "" || Number(form.actual_hours) >= 0;
  const dirty = Object.keys(changes).length > 0;
  return (
    <section aria-labelledby="the-work">
      <header className="section-title">
        <h3 id="the-work">The work</h3>
        <button type="button" className="primary small" disabled={busy || !dirty || !valid} onClick={() => onSave(changes)}>
          Save
        </button>
      </header>
      <div className="field">
        <label htmlFor="p-parts">Parts</label>
        <select id="p-parts" value={form.parts} onChange={(e) => setForm({ ...form, parts: e.target.value as Job["parts"] })}>
          <option value="none">None</option>
          <option value="on_truck">On the truck</option>
          <option value="special_order">Special order</option>
        </select>
      </div>
      <div className="field">
        <label htmlFor="p-pn">Part numbers</label>
        <input id="p-pn" value={form.part_numbers} onChange={(e) => setForm({ ...form, part_numbers: e.target.value })} placeholder="Comma separated" />
      </div>
      <div className="field">
        <label htmlFor="p-hours">Hours on site</label>
        <input id="p-hours" inputMode="decimal" value={form.actual_hours} onChange={(e) => setForm({ ...form, actual_hours: e.target.value })} />
      </div>
    </section>
  );
}

function ReviewForm({ busy, onCancel, onSubmit }: { busy: boolean; onCancel: () => void; onSubmit: (reason: string) => void }) {
  const [kind, setKind] = useState<Extenuating>("parts_delay");
  const [note, setNote] = useState("");
  const submit = (e: FormEvent) => {
    e.preventDefault();
    const label = REASONS.find((r) => r.value === kind)?.label ?? kind;
    onSubmit(note.trim() ? `${label}: ${note.trim()}` : label);
  };
  return (
    <form className="phone-form" onSubmit={submit}>
      <h3>Needs review</h3>
      <div className="field">
        <label htmlFor="r-kind">Why</label>
        <select id="r-kind" value={kind} onChange={(e) => setKind(e.target.value as Extenuating)}>
          {REASONS.map((r) => (
            <option key={r.value} value={r.value}>
              {r.label}
            </option>
          ))}
        </select>
      </div>
      <div className="field">
        <label htmlFor="r-note">One line for dispatch</label>
        <input id="r-note" value={note} onChange={(e) => setNote(e.target.value)} />
      </div>
      <button type="submit" className="primary block" disabled={busy}>
        Send for review
      </button>
      <button type="button" className="link-button" onClick={onCancel}>
        Cancel
      </button>
    </form>
  );
}

function CloseForm({ job, busy, onCancel, onSubmit }: { job: Job; busy: boolean; onCancel: () => void; onSubmit: (p: Record<string, unknown>) => void }) {
  const [hours, setHours] = useState(job.actual_hours == null ? "" : String(job.actual_hours));
  const [signed, setSigned] = useState(true);
  const [by, setBy] = useState("Store manager");
  const [why, setWhy] = useState("");
  const ok = Number(hours) > 0 && (signed ? by.trim() !== "" : why.trim() !== "");
  const submit = (e: FormEvent) => {
    e.preventDefault();
    onSubmit(signed ? { actual_hours: Number(hours), sign_off_by: by.trim() } : { actual_hours: Number(hours), no_sign_off_reason: why.trim() });
  };
  return (
    <form className="phone-form" onSubmit={submit}>
      <h3>Close job {job.number}</h3>
      <div className="field">
        <label htmlFor="c-hours">Hours on site</label>
        <input id="c-hours" inputMode="decimal" value={hours} onChange={(e) => setHours(e.target.value)} />
      </div>
      <fieldset className="choice">
        <legend>Sign-off</legend>
        <label>
          <input type="radio" checked={signed} onChange={() => setSigned(true)} /> The site signed off
        </label>
        <label>
          <input type="radio" checked={!signed} onChange={() => setSigned(false)} /> Nobody could sign
        </label>
      </fieldset>
      {signed ? (
        <div className="field">
          <label htmlFor="c-by">Signed by</label>
          <input id="c-by" value={by} onChange={(e) => setBy(e.target.value)} />
        </div>
      ) : (
        <div className="field">
          <label htmlFor="c-why">Why not</label>
          <input id="c-why" value={why} onChange={(e) => setWhy(e.target.value)} />
        </div>
      )}
      <button type="submit" className="primary block" disabled={busy || !ok}>
        Close and send to billing
      </button>
      <button type="button" className="link-button" onClick={onCancel}>
        Cancel
      </button>
    </form>
  );
}
