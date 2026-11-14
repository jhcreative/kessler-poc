// View 3, the controller queue (page 4; B1 to B3): closed jobs arrive with a drafted invoice in the client's format;
// approving it posts it to QuickBooks (simulated), and the aging moves.
import type { ColDef, RowClassParams } from "ag-grid-community";
import { AgGridReact } from "ag-grid-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ApiError, api } from "../api/client";
import type { Aging, InvoiceOut, Job, JobState } from "../api/types";
import { useAuth } from "../auth";
import { COMMAND_LABEL, STATE_LABEL, dollars, when } from "../format";
import { houseGrid } from "../grid/theme";
import { newestFirst } from "../live/store";
import { useLive } from "../live/useLive";
import { useToast } from "../Toast";
import { useDelayed } from "../useDelayed";
import { ViewTitle } from "./ViewTitle";

type Tab = "review" | "sent_back" | "submitted" | "paid";
const TABS: { key: Tab; label: string; states: JobState[] }[] = [
  { key: "review", label: "Billing review", states: ["billing_review"] },
  { key: "sent_back", label: "Sent back", states: ["closed"] },
  { key: "submitted", label: "Submitted", states: ["invoiced"] },
  { key: "paid", label: "Paid", states: ["paid"] },
];

function Money({ value }: { value: number | null | undefined }) {
  if (value == null) return null;
  return (
    <span>
      <span className="unit">$</span>
      {dollars(value)}
    </span>
  );
}

const columns: ColDef<Job>[] = [
  { field: "number", headerName: "Job", width: 72 },
  { field: "client_name", headerName: "Client", width: 170 },
  { field: "site_label", headerName: "Site", width: 200 },
  { field: "final_cents", headerName: "Final", width: 110, type: "rightAligned", cellRenderer: (p: { value: number | null }) => <Money value={p.value} /> },
  { field: "updated_at", hide: true, sort: "desc" },
];

const FORMAT_LABEL: Record<string, string> = {
  "bullseye-portal": "Bullseye portal",
  "starbrew-email-pdf": "Starbrew, PDF by email",
  "wellgreens-csv": "Wellgreens CSV",
  "cvr-portal": "CVR portal",
  "wegford-edi": "Wegford EDI",
  "aldo-pdf": "Aldo Foods PDF",
  "facilit-standard": "FacilIT standard",
};

export function Controller() {
  const { signedOut } = useAuth();
  const { state, status, loaded, error } = useLive({ onSignedOut: signedOut });
  const [tab, setTab] = useState<Tab>("review");
  const [selected, setSelected] = useState<string | null>(null);
  const [aging, setAging] = useState<Aging | null>(null);

  useEffect(() => {
    api.aging().then(setAging).catch(() => undefined); // moves with every approval and payment
  }, [state.lastEventId]);

  const all = useMemo(() => newestFirst(state.jobs), [state.jobs]);
  const current = TABS.find((t) => t.key === tab) ?? TABS[0]!;
  const rows = useMemo(() => all.filter((j) => current.states.includes(j.state)), [all, current]);
  const job = selected ? state.jobs.get(selected) ?? null : null;
  const skeleton = useDelayed(!loaded || !aging);
  const rowClassRules = useMemo(() => ({ "row-selected": (p: RowClassParams<Job>) => p.data?.id === selected }), [selected]);
  const getRowId = useCallback((p: { data: Job }) => p.data.id, []);

  return (
    <main className="workspace" aria-busy={!loaded}>
      <ViewTitle title="Controller" status={status} />
      {error && <p className="error-line" role="alert">{error}</p>}

      <section className="aging" aria-labelledby="aging-title">
        <h2 id="aging-title">
          Aging <span className="muted">QuickBooks (simulated), open invoices by days past due</span>
        </h2>
        <div className="tiles">
          {aging
            ? aging.buckets.map((b) => (
                <div className="tile static" key={b.label}>
                  <span className="count">
                    <Money value={b.amount_cents} />
                  </span>
                  <span className="name">{b.label}</span>
                  <span className="wait">
                    {b.count} invoice{b.count === 1 ? "" : "s"}
                  </span>
                </div>
              ))
            : skeleton && [0, 1, 2, 3, 4].map((i) => <div key={i} className="tile skeleton" aria-hidden="true" />)}
          {aging && (
            <div className="tile static total">
              <span className="count">
                <Money value={aging.open_cents} />
              </span>
              <span className="name">Open</span>
              <span className="wait">{aging.open_count} invoices</span>
            </div>
          )}
        </div>
      </section>

      <section className="queue-column" aria-label="Queues">
        <div role="tablist" className="tabs" aria-label="Queues">
          {TABS.map((t) => (
            <button key={t.key} role="tab" type="button" aria-selected={tab === t.key} onClick={() => setTab(t.key)}>
              {t.label} <span className="tab-count">{loaded ? all.filter((j) => t.states.includes(j.state)).length : ""}</span>
            </button>
          ))}
        </div>
        <div className="grid queue-grid short" role="tabpanel">
          {loaded ? (
            <AgGridReact<Job>
              theme={houseGrid}
              rowData={rows}
              columnDefs={columns}
              getRowId={getRowId}
              rowClassRules={rowClassRules}
              onRowClicked={(e) => e.data && setSelected(e.data.id)}
              suppressCellFocus
              overlayNoRowsTemplate="<span class='status-line'>Nothing here.</span>"
            />
          ) : (
            skeleton && Array.from({ length: 8 }, (_, i) => <div key={i} className="skeleton skeleton-row" aria-hidden="true" />)
          )}
        </div>
      </section>

      <section className="record-column short" aria-label="Invoice">
        {job ? <InvoicePanel key={job.id} job={job} /> : <p className="status-line pad">Choose a job to review its invoice.</p>}
      </section>
    </main>
  );
}

function InvoicePanel({ job }: { job: Job }) {
  const toast = useToast();
  const [invoice, setInvoice] = useState<InvoiceOut | null>(null);
  const [missing, setMissing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [sendingBack, setSendingBack] = useState(false);
  const [reason, setReason] = useState("");

  useEffect(() => {
    api
      .invoice(job.id)
      .then((i) => {
        setInvoice(i);
        setMissing(false);
      })
      .catch(() => setMissing(true));
  }, [job.id, job.last_event_id]);

  const run = async (command: string, payload: Record<string, unknown> = {}) => {
    setBusy(true);
    try {
      const r = await api.command(job.id, { command, expected_event_id: job.last_event_id, payload, override_reason: null });
      const doc = r.events[0]?.payload.qb_doc_number;
      toast(typeof doc === "string" ? `Submitted to QuickBooks (simulated) as ${doc}` : `${COMMAND_LABEL[command] ?? command}: job ${job.number}`);
      setSendingBack(false);
    } catch (e) {
      toast(e instanceof ApiError ? e.message : "That didn't go through", true);
    } finally {
      setBusy(false);
    }
  };

  return (
    <article className="record">
      <header className="record-title">
        <h2>
          Job {job.number} <span className="muted">{job.client_name}</span>
        </h2>
        <span className="state-pill">{STATE_LABEL[job.state]}</span>
        {job.state === "billing_review" && invoice && (
          <div className="actions">
            <button type="button" className="primary" disabled={busy || !invoice.check_passed} onClick={() => void run("approve_invoice")}>
              Approve and submit
            </button>
            <button type="button" className="secondary" disabled={busy} onClick={() => setSendingBack(true)}>
              Send back
            </button>
          </div>
        )}
      </header>

      {sendingBack && (
        <form
          className="inline-form"
          onSubmit={(e) => {
            e.preventDefault();
            void run("send_back_invoice", { reason: reason.trim() });
          }}
        >
          <div className="field">
            <label htmlFor="sb-reason">Why it goes back</label>
            <input id="sb-reason" value={reason} onChange={(e) => setReason(e.target.value)} />
          </div>
          <button type="submit" className="primary" disabled={busy || !reason.trim()}>
            Send back
          </button>
          <button type="button" className="link-button" onClick={() => setSendingBack(false)}>
            Cancel
          </button>
        </form>
      )}

      {missing && <p className="status-line">No invoice yet: it's drafted when the job closes.</p>}
      {invoice && (
        <div className="record-body">
          <p className={invoice.check_passed ? "check-line" : "rule-line"}>
            {invoice.check_passed ? "Passed the check: signed off, approved where the contract asks, within the estimate." : `Failed the check: ${invoice.check_note}. Send it back to the coordinator.`}
          </p>
          {invoice.qb_doc_number && <p className="check-line">Submitted to QuickBooks (simulated) as {invoice.qb_doc_number}.</p>}
          <section aria-labelledby="inv">
            <h3 id="inv">Invoice, {FORMAT_LABEL[invoice.format] ?? invoice.format} format</h3>
            <table className="lines">
              <tbody>
                {invoice.lines.map((l) => (
                  <tr key={l.desc}>
                    <td>{l.desc}</td>
                    <td className="num">
                      <Money value={l.cents} />
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <th scope="row">Total</th>
                  <td className="num">
                    <Money value={invoice.total_cents} />
                  </td>
                </tr>
              </tfoot>
            </table>
          </section>
          <section aria-labelledby="inv-job">
            <h3 id="inv-job">The job</h3>
            <dl className="facts">
              <dt>Site</dt>
              <dd>{job.site_label}</dd>
              <dt>Work order</dt>
              <dd>{job.client_wo}</dd>
              <dt>Purchase order</dt>
              <dd>{job.client_po ?? "None given"}</dd>
              <dt>Estimate</dt>
              <dd>
                <Money value={job.estimate_cents} />
              </dd>
              <dt>Signed off</dt>
              <dd>{job.sign_off ? `${job.sign_off.by}, ${when(job.sign_off.at)}` : "No"}</dd>
              {job.approval && (
                <>
                  <dt>Client approval</dt>
                  <dd>ref {job.approval.client_ref}</dd>
                </>
              )}
            </dl>
          </section>
        </div>
      )}
    </article>
  );
}
