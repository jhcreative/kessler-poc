// View 2, dispatch (page 4; D1 to D3, T4): approved jobs arrive live; each shows the recommended tech and why.
import type { ColDef, RowClassParams } from "ag-grid-community";
import { AgGridReact } from "ag-grid-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ApiError, api } from "../api/client";
import type { CandidateOut, Job, JobState, Recommendation, TechOut } from "../api/types";
import { useAuth } from "../auth";
import { COMMAND_LABEL, ISSUE_LABEL, STATE_LABEL, dollars, when } from "../format";
import { houseGrid } from "../grid/theme";
import { newestFirst } from "../live/store";
import { useLive } from "../live/useLive";
import { useToast } from "../Toast";
import { useDelayed } from "../useDelayed";
import { ViewTitle } from "./ViewTitle";

type Tab = "ready" | "review" | "board" | "techs";
const TABS: { key: Tab; label: string; states?: JobState[] }[] = [
  { key: "ready", label: "Ready", states: ["ready_for_dispatch"] },
  { key: "review", label: "Needs review", states: ["needs_review"] },
  { key: "board", label: "On the board", states: ["assigned", "onsite"] },
  { key: "techs", label: "Techs" },
];

const jobColumns: ColDef<Job>[] = [
  { field: "number", headerName: "Job", width: 72 },
  { field: "client_name", headerName: "Client", width: 150 },
  { field: "site_label", headerName: "Site", width: 190 },
  { field: "issue_type", headerName: "Issue", width: 110, valueFormatter: (p) => ISSUE_LABEL[String(p.value)] ?? "" },
  { field: "tech_label", headerName: "Tech", width: 90 },
  { field: "updated_at", hide: true, sort: "desc" },
];

const techColumns: ColDef<TechOut>[] = [
  { field: "label", headerName: "Tech", width: 90 },
  { field: "truck", headerName: "Truck", width: 80 },
  { field: "truck_status", headerName: "Truck is", width: 100, valueFormatter: (p) => (p.value === "onsite" ? "On site" : p.value === "driving" ? "Driving" : "Parked") },
  { field: "load", headerName: "Board", width: 80 },
  { field: "skills", headerName: "Skills", width: 220, valueFormatter: (p) => ((p.value as string[] | undefined) ?? []).map((s) => ISSUE_LABEL[s] ?? s).join(", ") },
  { field: "licenses", headerName: "Licensed in", width: 120, valueFormatter: (p) => ((p.value as string[] | undefined) ?? []).join(", ") },
];

export function Dispatch() {
  const { signedOut } = useAuth();
  const { state, status, loaded, error } = useLive({ onSignedOut: signedOut });
  const [tab, setTab] = useState<Tab>("ready");
  const [selected, setSelected] = useState<string | null>(null);
  const [roster, setRoster] = useState<TechOut[]>([]);

  useEffect(() => {
    api.techs().then(setRoster).catch(() => undefined); // loads change with every assignment
  }, [state.lastEventId]);

  const all = useMemo(() => newestFirst(state.jobs), [state.jobs]);
  const inTab = (t: (typeof TABS)[number]) => all.filter((j) => t.states?.includes(j.state));
  const current = TABS.find((t) => t.key === tab) ?? TABS[0]!;
  const rows = useMemo(() => all.filter((j) => current.states?.includes(j.state)), [all, current]);
  const job = selected ? state.jobs.get(selected) ?? null : null;
  const skeleton = useDelayed(!loaded);
  const rowClassRules = useMemo(() => ({ "row-selected": (p: RowClassParams<Job>) => p.data?.id === selected }), [selected]);
  const getRowId = useCallback((p: { data: Job }) => p.data.id, []);
  const getTechId = useCallback((p: { data: TechOut }) => p.data.id, []);

  return (
    <main className="workspace" aria-busy={!loaded}>
      <ViewTitle title="Dispatch" status={status} />
      {error && <p className="error-line" role="alert">{error}</p>}
      <section className="queue-column" aria-label="Queues">
        <div role="tablist" className="tabs" aria-label="Queues">
          {TABS.map((t) => (
            <button key={t.key} role="tab" type="button" aria-selected={tab === t.key} onClick={() => setTab(t.key)}>
              {t.label} <span className="tab-count">{!loaded ? "" : t.states ? inTab(t).length : roster.length}</span>
            </button>
          ))}
        </div>
        <div className="grid queue-grid" role="tabpanel">
          {!loaded ? (
            skeleton && Array.from({ length: 8 }, (_, i) => <div key={i} className="skeleton skeleton-row" aria-hidden="true" />)
          ) : tab === "techs" ? (
            <AgGridReact<TechOut> key="techs" theme={houseGrid} rowData={roster} columnDefs={techColumns} getRowId={getTechId} suppressCellFocus />
          ) : (
            <AgGridReact<Job>
              key="jobs"
              theme={houseGrid}
              rowData={rows}
              columnDefs={jobColumns}
              getRowId={getRowId}
              rowClassRules={rowClassRules}
              onRowClicked={(e) => e.data && setSelected(e.data.id)}
              suppressCellFocus
              overlayNoRowsTemplate="<span class='status-line'>Nothing waiting here.</span>"
            />
          )}
        </div>
      </section>
      <section className="record-column" aria-label="Job">
        {job ? <DispatchRecord key={job.id} job={job} /> : <p className="status-line pad">Choose a job to see who should take it.</p>}
      </section>
    </main>
  );
}

function DispatchRecord({ job }: { job: Job }) {
  const toast = useToast();
  const [rec, setRec] = useState<Recommendation | null>(null);
  const [busy, setBusy] = useState(false);
  const deciding = job.state === "ready_for_dispatch" || job.state === "needs_review";

  useEffect(() => {
    if (!deciding) return setRec(null);
    api.recommendation(job.id).then(setRec).catch(() => setRec(null));
  }, [job.id, job.last_event_id, deciding]);

  const run = async (command: string, payload: Record<string, unknown> = {}, override: string | null = null) => {
    setBusy(true);
    try {
      await api.command(job.id, { command, expected_event_id: job.last_event_id, payload, override_reason: override });
      const who = typeof payload.tech === "string" ? ` to ${payload.tech}` : "";
      toast(`${COMMAND_LABEL[command] ?? command}${who}: job ${job.number}`);
    } catch (e) {
      toast(e instanceof ApiError ? e.message : "That didn't go through", true);
    } finally {
      setBusy(false);
    }
  };
  const assignCommand = job.state === "needs_review" ? "reassign_tech" : "assign_tech";
  const top = rec?.top ?? null;

  return (
    <article className="record">
      <header className="record-title">
        <h2>
          Job {job.number} <span className="muted">{job.client_name}</span>
        </h2>
        <span className="state-pill">{STATE_LABEL[job.state]}</span>
        <div className="actions">
          {top && (
            <button type="button" className="primary" disabled={busy} onClick={() => void run(assignCommand, { tech: top.label })}>
              {job.state === "needs_review" ? `Reassign to ${top.label}` : `Assign ${top.label}`}
            </button>
          )}
          {job.state === "needs_review" && (
            <>
              <button type="button" className="secondary" disabled={busy} onClick={() => void run("ask_to_wait")}>
                Ask tech to wait
              </button>
              <button type="button" className="secondary" disabled={busy} onClick={() => void run("return_to_dispatch")}>
                Return to dispatch
              </button>
            </>
          )}
        </div>
      </header>

      <div className="record-body">
        <section aria-labelledby="the-job">
          <h3 id="the-job">The job</h3>
          <dl className="facts">
            <dt>Site</dt>
            <dd>{job.site_label}</dd>
            <dt>Issue</dt>
            <dd>{ISSUE_LABEL[job.issue_type] ?? job.issue_type}</dd>
            <dt>Estimate</dt>
            <dd>
              <span className="unit">$</span>
              {dollars(job.estimate_cents)}
            </dd>
            {job.tech_label && (
              <>
                <dt>Tech</dt>
                <dd>{job.tech_label}</dd>
              </>
            )}
            {job.window_start && (
              <>
                <dt>Window</dt>
                <dd>{when(job.window_start)}</dd>
              </>
            )}
            {job.state === "needs_review" && (
              <>
                <dt>Why review</dt>
                <dd>{job.extenuating_note ?? "No reason given"}</dd>
              </>
            )}
          </dl>
        </section>

        {deciding && (
          <section aria-labelledby="who">
            <h3 id="who">Who should take it</h3>
            {!rec ? (
              <div className="skeleton" style={{ height: 120 }} aria-hidden="true" />
            ) : top ? (
              <div className="recommended">
                <p className="recommended-name">
                  Recommended: <strong>{top.label}</strong>
                </p>
                <ul>
                  {top.reasons.map((r) => (
                    <li key={r}>{r}</li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="rule-line">Nobody has both the skill and a license in {job.site_state}. Pick a tech below and give the reason.</p>
            )}
            {rec && (
              <ol className="candidates" aria-label="Other techs">
                {rec.candidates
                  .filter((c) => c.tech_id !== top?.tech_id)
                  .map((c) => (
                    <CandidateRow key={c.tech_id} c={c} busy={busy} onAssign={(reason) => void run(assignCommand, { tech: c.label }, reason)} />
                  ))}
              </ol>
            )}
          </section>
        )}
      </div>
    </article>
  );
}

// A tech who doesn't qualify can still be picked, with a reason that goes on record (the soft rail).
function CandidateRow({ c, busy, onAssign }: { c: CandidateOut; busy: boolean; onAssign: (reason: string | null) => void }) {
  const [asking, setAsking] = useState(false);
  const [reason, setReason] = useState("");
  return (
    <li className="candidate" data-eligible={c.eligible || undefined}>
      <span className="candidate-name">{c.label}</span>
      <span className="muted">
        {Math.round(c.distance_km)} km, board {c.load}
        {c.gaps.length > 0 && `: ${c.gaps.join(", ")}`}
      </span>
      {!asking ? (
        <button type="button" className="link-button" disabled={busy} onClick={() => (c.eligible ? onAssign(null) : setAsking(true))}>
          Assign
        </button>
      ) : (
        <span className="override">
          <input aria-label={`Why assign ${c.label}`} placeholder="Why, for the record" value={reason} onChange={(e) => setReason(e.target.value)} />
          <button type="button" className="secondary small" disabled={busy || !reason.trim()} onClick={() => onAssign(reason.trim())}>
            Assign anyway
          </button>
        </span>
      )}
    </li>
  );
}
