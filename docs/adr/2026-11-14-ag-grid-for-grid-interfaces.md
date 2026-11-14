# 2026-11-14: AG Grid for grid interfaces, not a hand-rolled grid

## Status
Accepted (John, 2026-11-14). It's the model for commercial clients with large data sets after this project, so it is a
candidate for a Tailor or agency ADR once the POC has proven it.

## Context
The POC's views are mostly grids: the overview of every job by queue and state, the coordinator's queues, dispatch's
ready list, and the controller's billing queue. House convention prefers owning a small hand-rolled component to taking
on a large dependency ("hand-rolled over hacked"; V-4). Commercial clients run large data sets, and a grid that sorts,
filters, pins, virtualizes and stays fast at tens of thousands of rows is a product in itself.

## Decision
We will use **AG Grid** (React) for grid interfaces in the POC and, after it, as the real-world model for commercial
clients with large data sets. We will not hand-roll grids.

## Consequences
### Positive
- Sorting, filtering, column state, row virtualization and live row updates come built in. Live row updates fit the
  websocket event flow: a job event updates one row in place.
- One grid model across every view, and across future client work.

### Negative
- A large dependency, which runs against V-4. This ADR is the recorded exception, not drift.
- **Licensing.** AG Grid Community is MIT-licensed. Enterprise (server-side row model, row grouping, pivoting, Excel
  export) is a paid commercial license, and John prefers to avoid paid subscriptions. **The POC uses Community only.**
  For large data sets, Community's infinite row model plus server-side filtering in our API covers it. Whether a
  client ever needs Enterprise is that client's decision and license.

### Risks
- The grid's look must meet the house UI canon (PQ-9..34). Jony themes it with our tokens and doesn't accept the stock
  theme.
- **Version pinning.** The exact version is pinned at install, at least two weeks old, and recorded in the lockfile
  (Cesar). Orly reviews the dependency at the RTS-6 check.

## Positions
**John (product owner):** "also thinking we introduce ag-grid here for grid type interfaces and NOT hand roll - this
will be real world model after this project for commercial clients with large data sets"

**Nathan (frontend lead):** Agreed for grids. Everything around the grid (the job record form, the tech's phone view)
stays hand-rolled on Tailor's components.

**Cesar (technical director):** Community only, pinned. Promote to a Tailor ADR after Monday if it earns its place.

## Participants
John (decision); Nathan, Cesar, Orly, Jony; Pete (record).
