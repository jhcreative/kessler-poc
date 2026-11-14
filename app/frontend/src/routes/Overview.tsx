// The one overview (G3, N4): every job by queue and state, live, with how long each step takes (Q9).
import type { ColDef, ICellRendererParams } from "ag-grid-community";
import { AgGridReact } from "ag-grid-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Navigate } from "react-router";
import { api } from "../api/client";
import type { Job, JobState, Overview as OverviewData } from "../api/types";
import { useAuth } from "../auth";
import { ISSUE_LABEL, QUEUE_LABEL, STATE_LABEL, dollars, hours, when } from "../format";
import { houseGrid } from "../grid/theme";
import { newestFirst } from "../live/store";
import { useLive } from "../live/useLive";
import { useDelayed } from "../useDelayed";
import { ViewTitle } from "./ViewTitle";

function Money({ value }: ICellRendererParams<Job, number | null>) {
  if (value == null) return null;
  return (
    <span>
      <span className="unit">$</span>
      {dollars(value)}
    </span>
  );
}

const columns: ColDef<Job>[] = [
  { field: "number", headerName: "Job", width: 90, sort: undefined },
  { field: "client_name", headerName: "Client", width: 190 },
  { field: "site_label", headerName: "Site", width: 260 },
  { field: "state", headerName: "State", width: 190, valueFormatter: (p) => (p.value ? STATE_LABEL[p.value as JobState] : "") },
  { field: "issue_type", headerName: "Issue", width: 140, valueFormatter: (p) => ISSUE_LABEL[String(p.value)] ?? String(p.value) },
  { field: "estimate_cents", headerName: "Estimate", width: 120, cellRenderer: Money, type: "rightAligned" },
  { field: "owner_label", headerName: "Coordinator", width: 140 },
  { field: "tech_label", headerName: "Tech", width: 100 },
  { field: "updated_at", headerName: "Updated", width: 140, sort: "desc", valueFormatter: (p) => (p.value ? when(String(p.value)) : "") },
];

export function Overview() {
  const { me } = useAuth();
  if (me?.role === "tech") return <Navigate to="/ops/tech" replace />; // the overview is for the office
  return <Board />;
}

function Board() {
  const { signedOut } = useAuth();
  const { state, status, loaded, error } = useLive({ onSignedOut: signedOut });
  const [steps, setSteps] = useState<OverviewData | null>(null);
  const [filter, setFilter] = useState<JobState | null>(null);
  const grid = useRef<AgGridReact<Job>>(null);

  // The step timings refresh with the board, at most every 3 s.
  const lastFetch = useRef(0);
  useEffect(() => {
    const due = Math.max(0, 3000 - (Date.now() - lastFetch.current));
    const t = window.setTimeout(() => {
      lastFetch.current = Date.now();
      api.overview().then(setSteps).catch(() => undefined);
    }, due);
    return () => window.clearTimeout(t);
  }, [state.lastEventId]);

  const rows = useMemo(() => newestFirst(state.jobs).filter((j) => !filter || j.state === filter), [state.jobs, filter]);

  // A changed row flashes once and settles (plan §6): the eye catches the update.
  const flashedSeen = useRef(new Map<string, number>());
  useEffect(() => {
    const api = grid.current?.api;
    if (!api) return;
    const nodes = [...state.flashed]
      .filter(([id, ev]) => flashedSeen.current.get(id) !== ev)
      .map(([id]) => api.getRowNode(id))
      .filter((n) => n != null);
    for (const [id, ev] of state.flashed) flashedSeen.current.set(id, ev);
    if (nodes.length) api.flashCells({ rowNodes: nodes, flashDuration: 900, fadeDuration: 900 });
  }, [state.flashed, rows]);

  const queues = useMemo(() => {
    const out = new Map<string, OverviewData["steps"]>();
    for (const s of steps?.steps ?? []) out.set(s.queue, [...(out.get(s.queue) ?? []), s]);
    return [...out];
  }, [steps]);
  const counts = useMemo(() => {
    const c = new Map<JobState, number>();
    for (const j of state.jobs.values()) c.set(j.state, (c.get(j.state) ?? 0) + 1);
    return c;
  }, [state.jobs]);
  const getRowId = useCallback((p: { data: Job }) => p.data.id, []);
  const skeleton = useDelayed(!loaded || !steps);

  return (
    <main aria-busy={!loaded}>
      <ViewTitle title="Overview" status={status} />
      {error && <p className="error-line" role="alert">{error}</p>}
      {skeleton && <span className="sr-only" role="status">Loading the board</span>}

      <section className="queues" aria-label="Jobs by queue and state">
        {loaded && steps
          ? queues.map(([queue, list]) => (
              <div className="queue" key={queue}>
                <h2>{QUEUE_LABEL[queue] ?? queue}</h2>
                <div className="tiles">
                  {list.map((s) => (
                    <button
                      key={s.state}
                      type="button"
                      className="tile"
                      aria-pressed={filter === s.state}
                      onClick={() => setFilter(filter === s.state ? null : s.state)}
                    >
                      <span className="count">{counts.get(s.state) ?? 0}</span>
                      <span className="name">{STATE_LABEL[s.state]}</span>
                      {s.state !== "paid" && s.open > 0 && s.open_hours_avg != null && (
                        <span className="wait">Avg wait {hours(s.open_hours_avg)}</span> // paid is the end: nothing waits
                      )}
                      {s.done_hours_median != null && <span className="wait">Usually {hours(s.done_hours_median)}</span>}
                    </button>
                  ))}
                </div>
              </div>
            ))
          : skeleton && [4, 1, 2, 2, 1, 1].map((n, i) => (
              <div className="queue" key={i} aria-hidden="true">
                <div className="skeleton" style={{ width: 90, height: 14 }} />
                <div className="tiles">
                  {Array.from({ length: n }, (_, k) => (
                    <div key={k} className="tile skeleton" />
                  ))}
                </div>
              </div>
            ))}
      </section>

      <div className="filters">
        <span className="showing">
          {loaded ? `${rows.length} of ${state.jobs.size} jobs${filter ? `, ${STATE_LABEL[filter]}` : ""}` : ""}
        </span>
        {filter && (
          <button type="button" className="link-button" onClick={() => setFilter(null)}>
            Clear Filter
          </button>
        )}
      </div>

      <div className="grid">
        {loaded ? (
          <AgGridReact<Job>
            ref={grid}
            theme={houseGrid}
            rowData={rows}
            columnDefs={columns}
            getRowId={getRowId}
            defaultColDef={{ sortable: true, resizable: true, filter: true }}
            suppressCellFocus
            animateRows={false}
          />
        ) : (
          skeleton && (
            <div aria-hidden="true">
              {Array.from({ length: 10 }, (_, i) => (
                <div key={i} className="skeleton skeleton-row" />
              ))}
            </div>
          )
        )}
      </div>
    </main>
  );
}
