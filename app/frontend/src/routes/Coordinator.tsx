// View 1, the coordinator workspace (page 4; C1, C2, C3): the queues on the left, one job record on the right.
// Everything moves through commands; the record updates live from the socket, whoever changed it.
import type { ColDef, RowClassParams } from "ag-grid-community";
import { AgGridReact } from "ag-grid-react";
import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { ApiError, api } from "../api/client";
import type { ContractOut, EventEnvelope, FieldsIn, Job, JobState } from "../api/types";
import { useAuth } from "../auth";
import { COMMAND_LABEL, ISSUE_CODE, ISSUE_LABEL, STATE_LABEL, dollars, hours, when } from "../format";
import { houseGrid } from "../grid/theme";
import { newestFirst } from "../live/store";
import { useLive } from "../live/useLive";
import { useToast } from "../Toast";
import { useDelayed } from "../useDelayed";
import { ViewTitle } from "./ViewTitle";

type QueueKey = "drafts" | "mine" | "approval" | "review" | "all";

// Five at most (PQ-27).
const QUEUES: { key: QueueKey; label: string; test: (j: Job, me: string) => boolean }[] = [
  { key: "drafts", label: "Drafts", test: (j) => j.state === "intake_draft" },
  { key: "mine", label: "Mine", test: (j, me) => j.owner_id === me && j.state !== "paid" },
  {
    key: "approval",
    label: "Needs approval",
    test: (j) => j.state === "needs_client_approval" || (j.state === "qualified" && j.requires_approval && !j.approval),
  },
  { key: "review", label: "Needs review", test: (j) => j.state === "needs_review" },
  { key: "all", label: "All", test: () => true },
];

// Fits the half-width column without a hidden scroll (PQ-15). Updated is hidden but still sorts: newest first (PQ-29).
const columns: ColDef<Job>[] = [
  { field: "number", headerName: "Job", width: 72 },
  { field: "client_name", headerName: "Client", width: 150 },
  { field: "site_label", headerName: "Site", width: 190 },
  { field: "state", headerName: "State", width: 150, valueFormatter: (p) => (p.value ? STATE_LABEL[p.value as JobState] : "") },
  { field: "issue_type", headerName: "Issue", width: 110, valueFormatter: (p) => ISSUE_LABEL[String(p.value)] ?? "" },
  { field: "updated_at", hide: true, sort: "desc" },
];

export function Coordinator() {
  const { me, signedOut } = useAuth();
  const { state, status, loaded, error } = useLive({ onSignedOut: signedOut });
  const toast = useToast();
  const [queue, setQueue] = useState<QueueKey>("drafts");
  const [selected, setSelected] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const myId = me?.person_id ?? "";

  const all = useMemo(() => newestFirst(state.jobs), [state.jobs]);
  const counts = useMemo(
    () => Object.fromEntries(QUEUES.map((q) => [q.key, all.filter((j) => q.test(j, myId)).length])),
    [all, myId],
  );
  const rows = useMemo(() => all.filter((j) => QUEUES.find((q) => q.key === queue)?.test(j, myId)), [all, queue, myId]);
  const job = selected ? state.jobs.get(selected) ?? null : null;
  const skeleton = useDelayed(!loaded);

  const newRequest = async () => {
    setSending(true);
    try {
      const r = await api.simulateRequest();
      setQueue("drafts");
      setSelected(r.job.id);
      const by = r.job.drafted_by === "claude" ? "Claude" : "the rules";
      toast(`New request from ${r.job.client_name}, drafted by ${by}`);
    } catch (e) {
      toast(e instanceof Error ? e.message : "The request didn't arrive", true);
    } finally {
      setSending(false);
    }
  };

  const rowClassRules = useMemo(() => ({ "row-selected": (p: RowClassParams<Job>) => p.data?.id === selected }), [selected]);
  const getRowId = useCallback((p: { data: Job }) => p.data.id, []);

  return (
    <main className="workspace" aria-busy={!loaded}>
      <ViewTitle title="Coordinator" status={status}>
        <button type="button" className="primary" onClick={() => void newRequest()} disabled={sending}>
          New request
        </button>
      </ViewTitle>
      {error && <p className="error-line" role="alert">{error}</p>}

      <section className="queue-column" aria-label="Queues">
        <div role="tablist" className="tabs" aria-label="Queues">
          {QUEUES.map((q) => (
            <button key={q.key} role="tab" type="button" aria-selected={queue === q.key} onClick={() => setQueue(q.key)}>
              {q.label} <span className="tab-count">{loaded ? counts[q.key] : ""}</span>
            </button>
          ))}
        </div>
        <div className="grid queue-grid" role="tabpanel">
          {loaded ? (
            <AgGridReact<Job>
              theme={houseGrid}
              rowData={rows}
              columnDefs={columns}
              getRowId={getRowId}
              rowClassRules={rowClassRules}
              onRowClicked={(e) => e.data && setSelected(e.data.id)}
              defaultColDef={{ sortable: true, resizable: true }}
              suppressCellFocus
              overlayNoRowsTemplate="<span class='status-line'>Nothing in this queue.</span>"
            />
          ) : (
            skeleton && Array.from({ length: 8 }, (_, i) => <div key={i} className="skeleton skeleton-row" aria-hidden="true" />)
          )}
        </div>
      </section>

      <section className="record-column" aria-label="Job record">
        {job ? <JobRecord key={job.id} job={job} /> : <p className="status-line pad">Choose a job to open its record.</p>}
      </section>
    </main>
  );
}

function JobRecord({ job }: { job: Job }) {
  const toast = useToast();
  const [events, setEvents] = useState<EventEnvelope[]>([]);
  const [contract, setContract] = useState<ContractOut | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.contract(job.id).then(setContract).catch(() => setContract(null));
  }, [job.id]);
  useEffect(() => {
    api.events(job.id).then((e) => setEvents([...e].reverse())).catch(() => undefined); // newest first (PQ-29)
  }, [job.id, job.last_event_id]);

  const run = async (command: string, payload: Record<string, unknown> = {}, done?: string) => {
    setBusy(true);
    try {
      await api.command(job.id, { command, expected_event_id: job.last_event_id, payload, override_reason: null });
      toast(done ?? `${COMMAND_LABEL[command] ?? command}: job ${job.number}`);
    } catch (e) {
      toast(e instanceof ApiError ? e.message : "That didn't go through", true);
    } finally {
      setBusy(false);
    }
  };

  const draftEvent = events.find((e) => e.command === "draft_intake");
  const drafted = draftEvent?.payload as { drafted_by?: string; model?: string; input_tokens?: number; output_tokens?: number; fallback_reason?: string } | undefined;
  const blockedByApproval = job.requires_approval && !job.approval;

  return (
    <article className="record">
      <header className="record-title">
        <h2>
          Job {job.number} <span className="muted">{job.client_name}</span>
        </h2>
        <span className="state-pill">{STATE_LABEL[job.state]}</span>
        <div className="actions">
          {job.state === "intake_draft" && (
            <button type="button" className="primary" disabled={busy} onClick={() => void run("qualify")}>
              Qualify
            </button>
          )}
          {job.state === "qualified" && blockedByApproval && (
            <button type="button" className="primary" disabled={busy} onClick={() => void run("request_client_approval")}>
              Request client approval
            </button>
          )}
          {job.state === "qualified" && (
            <button
              type="button"
              className={blockedByApproval ? "secondary" : "primary"}
              disabled={busy || blockedByApproval}
              onClick={() => void run("approve_for_dispatch")}
            >
              Approve for dispatch
            </button>
          )}
          {job.state === "closed" && (
            <button type="button" className="primary" disabled={busy} onClick={() => void run("draft_invoice", {}, `Redrafted the invoice: job ${job.number}`)}>
              Redraft invoice
            </button>
          )}
          {job.state === "needs_review" && (
            <>
              <button type="button" className="primary" disabled={busy} onClick={() => void run("ask_to_wait")}>
                Ask tech to wait
              </button>
              <button type="button" className="secondary" disabled={busy} onClick={() => void run("return_to_dispatch")}>
                Return to dispatch
              </button>
            </>
          )}
        </div>
      </header>

      {drafted && (
        <p className="drafted" data-by={drafted.drafted_by}>
          {drafted.drafted_by === "claude"
            ? `Drafted by Claude from source (${drafted.model ?? "Claude"}, ${drafted.input_tokens ?? 0} in, ${drafted.output_tokens ?? 0} out tokens). Check it against the request below.`
            : `Drafted by the rules from source: ${drafted.fallback_reason ?? "Claude wasn't used"}. Check it against the request below.`}
        </p>
      )}

      {job.state === "needs_client_approval" && <ApprovalForm busy={busy} onSubmit={(p) => void run("record_client_approval", p)} />}
      {blockedByApproval && job.state !== "needs_client_approval" && (
        <p className="rule-line">{job.rule_fired}. The client's approval goes on record before dispatch.</p>
      )}

      <div className="record-body">
        <section aria-labelledby="identity">
          <h3 id="identity">From the request</h3>
          <dl className="facts">
            <dt>Site</dt>
            <dd>{job.site_label}</dd>
            <dt>Work order</dt>
            <dd>{job.client_wo}</dd>
            <dt>Purchase order</dt>
            <dd>{job.client_po ?? "None given"}</dd>
            <dt>Site contact</dt>
            <dd>{job.site_contact}</dd>
            <dt>Came in by</dt>
            <dd>{job.source === "facilit" ? "FacilIT" : job.source === "portal" ? "Client portal" : "Email"}</dd>
          </dl>
          <details className="source">
            <summary>The request as it arrived</summary>
            <pre>{job.source_text}</pre>
          </details>
        </section>

        <WorkingFields job={job} contract={contract} busy={busy} onSave={(changes) => void run("update_fields", changes, `Saved job ${job.number}`)} />

        <section aria-labelledby="contract">
          <h3 id="contract">Contract</h3>
          {contract ? (
            <dl className="facts">
              {contract.rules.map((r) => (
                <div key={r.text} style={{ display: "contents" }}>
                  <dt>{r.kind === "cap" ? "Cap" : "Review"}</dt>
                  <dd>{r.text}</dd>
                </div>
              ))}
              <dt>Terms</dt>
              <dd>Net {contract.net_days}</dd>
              <dt>Invoice</dt>
              <dd>{contract.invoice_format}</dd>
            </dl>
          ) : (
            <div className="skeleton" style={{ height: 72 }} aria-hidden="true" />
          )}
          {job.approval && (
            <p className="status-line">
              Approved by {job.approval.by}, ref {job.approval.client_ref}, {when(job.approval.at)}
            </p>
          )}
        </section>

        <section aria-labelledby="history">
          <h3 id="history">History</h3>
          <ol className="history">
            {events.map((e) => (
              <li key={e.id}>
                <span className="when">{when(e.at)}</span> <strong>{COMMAND_LABEL[e.command] ?? e.command}</strong>{" "}
                <span className="muted">by {e.actor.label}</span>
                {e.override_reason && <span className="muted"> (override: {e.override_reason})</span>}
              </li>
            ))}
          </ol>
        </section>
      </div>
    </article>
  );
}

function ApprovalForm({ busy, onSubmit }: { busy: boolean; onSubmit: (p: { by: string; client_ref: string }) => void }) {
  const [by, setBy] = useState("Client facilities manager");
  const [ref, setRef] = useState("");
  const submit = (e: FormEvent) => {
    e.preventDefault();
    onSubmit({ by, client_ref: ref });
  };
  return (
    <form className="inline-form" onSubmit={submit}>
      <div className="field">
        <label htmlFor="appr-by">Approved by</label>
        <input id="appr-by" value={by} onChange={(e) => setBy(e.target.value)} />
      </div>
      <div className="field">
        <label htmlFor="appr-ref">Client reference</label>
        <input id="appr-ref" value={ref} onChange={(e) => setRef(e.target.value)} placeholder="From the client's portal or email" />
      </div>
      <button type="submit" className="primary" disabled={busy || !by.trim() || !ref.trim()}>
        Record approval
      </button>
    </form>
  );
}

// Part B: the working fields, the same typed fields in every view. Only changed fields are sent.
function WorkingFields({ job, contract, busy, onSave }: { job: Job; contract: ContractOut | null; busy: boolean; onSave: (c: FieldsIn) => void }) {
  const initial = useMemo(
    () => ({
      issue_type: ISSUE_LABEL[job.issue_type] ?? job.issue_type,
      estimate: String(Math.round(job.estimate_cents / 100)),
      est_hours: job.est_hours == null ? "" : String(job.est_hours),
      parts: job.parts,
      part_numbers: job.part_numbers.join(", "),
      extenuating_note: job.extenuating_note ?? "",
    }),
    [job],
  );
  const [form, setForm] = useState(initial);
  useEffect(() => setForm(initial), [initial]); // someone else changed the job: show the new truth
  const final = job.state === "invoiced" || job.state === "paid";
  const estimate = Number(form.estimate);
  const issueCode = ISSUE_CODE[form.issue_type.trim().toLowerCase()];
  const issueOk = issueCode !== undefined && (!contract || contract.issue_types.includes(issueCode));
  const valid = Number.isFinite(estimate) && estimate >= 0 && (form.est_hours === "" || Number(form.est_hours) >= 0) && issueOk;
  const changes: FieldsIn = {};
  if (form.issue_type !== initial.issue_type && issueCode) changes.issue_type = issueCode;
  if (form.estimate !== initial.estimate) changes.estimate_cents = Math.round(estimate * 100);
  if (form.est_hours !== initial.est_hours) changes.est_hours = form.est_hours === "" ? null : Number(form.est_hours);
  if (form.parts !== initial.parts) changes.parts = form.parts;
  if (form.part_numbers !== initial.part_numbers) changes.part_numbers = form.part_numbers.split(",").map((s) => s.trim()).filter(Boolean);
  if (form.extenuating_note !== initial.extenuating_note) changes.extenuating_note = form.extenuating_note || null;
  const dirty = Object.keys(changes).length > 0;
  const set = (k: keyof typeof form) => (e: { target: { value: string } }) => setForm({ ...form, [k]: e.target.value });

  return (
    <section aria-labelledby="working">
      <header className="section-title">
        <h3 id="working">The work</h3>
        {!final && (
          <button type="button" className="primary small" disabled={busy || !dirty || !valid} onClick={() => onSave(changes)}>
            Save
          </button>
        )}
      </header>
      <fieldset className="field-grid" disabled={final || busy}>
        <div className="field">
          <label htmlFor="f-issue">Issue type</label>
          <input id="f-issue" list="issue-types" value={form.issue_type} onChange={set("issue_type")} placeholder="Type to choose" aria-invalid={issueOk ? undefined : true} />
          <datalist id="issue-types">
            {(contract?.issue_types ?? []).map((t) => (
              <option key={t} value={ISSUE_LABEL[t] ?? t} />
            ))}
          </datalist>
        </div>
        <div className="field">
          <label htmlFor="f-est">Estimate ($)</label>
          <input id="f-est" inputMode="numeric" value={form.estimate} onChange={set("estimate")} />
        </div>
        <div className="field">
          <label htmlFor="f-hours">Estimated hours</label>
          <input id="f-hours" inputMode="decimal" value={form.est_hours} onChange={set("est_hours")} />
        </div>
        <div className="field">
          <label htmlFor="f-parts">Parts</label>
          <select id="f-parts" value={form.parts} onChange={set("parts")}>
            <option value="none">None</option>
            <option value="on_truck">On the truck</option>
            <option value="special_order">Special order</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="f-pn">Part numbers</label>
          <input id="f-pn" value={form.part_numbers} onChange={set("part_numbers")} placeholder="Comma separated" />
        </div>
        <div className="field wide">
          <label htmlFor="f-note">Extenuating circumstances</label>
          <input id="f-note" value={form.extenuating_note} onChange={set("extenuating_note")} />
        </div>
      </fieldset>
      {job.actual_hours != null && <p className="status-line">Actual hours on site: {hours(job.actual_hours)}</p>}
      {job.final_cents != null && (
        <p className="status-line">
          Final: <span className="unit">$</span>
          {dollars(job.final_cents)}
        </p>
      )}
    </section>
  );
}
