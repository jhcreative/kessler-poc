# Carry-forward 2026-11-14: plan approved; the build starts in a new window (Anne)

## State

Nothing live, and no build code yet. **The POC plan is approved (T3, John, 2026-11-14)**:
`docs/plans/2026-11-13-poc-plan.md`. Every walkthrough answer is in `docs/plans/2026-11-13-poc-plan-walkthrough.md`.
Due Monday 2026-11-16. The dry-run report is due Sunday 8 pm.

## Start here, in the new window

1. **Read these, in order:**
   1. `CLAUDE.md`;
   2. `docs/status.md`;
   3. the plan, §2 (goals and the W2 outcome), §4–§9, §11 and §11a;
   4. `docs/backlog/README.md`;
   5. ADRs `2026-11-12-a-harness-with-adapters-not-a-core.md` and `2026-11-14-ag-grid-for-grid-interfaces.md`.
2. **Sprint start: check RTS-1..6** (plan §13) and record the result.
3. **POC-02 (Cesar).** Scaffold the Tailor instance with `node ~/jhc/tailor/scaffold/scaffold.js` into
   `~/jhc/sites/jahnel-poc` (`~/jhc/tailor/docs/runbooks/build-a-site.md`).
   - Then prove the seam for an instance-local own-table module `fieldops`, shaped like `~/jhc/tailor/modules/ecom`
     (ADR-0038, ADR-0040). This is risk R3.
   - Fallback: plain instance routes with the same tables.
   - Never put POC code in Tailor core.
4. **Then, in rank order:** POC-03 tables and seed (Pete, Jen), POC-04 commands and the state machine with tests,
   POC-05 the WebSocket hub and replay, then the views.
5. **Before writing the Claude drafting call, load the `claude-api` skill.** It sets the model choice, a Sonnet-class
   default for extraction.

## What John decided in the walkthrough (the short list)

- **Narratives:** happy path first, and a Playwright narrative per view: coordinator, then dispatch and onsite, then
  controller, then the overview for executives.
- **Scope:** breadth over depth. No option trees and no time-tracking sub-views.
- **Grids:** AG Grid Community only, until future demand. Everything else is hand-rolled on Tailor's components.
- **Box and name:** a new OVH VPS-2 as JHC's apps box (edge mode), with `apps.johnhiemstra.com` as the home and this POC
  at `ofs.apps.johnhiemstra.com`. curationapp.com goes on the box after Monday.
- **Intake:** Claude drafts it, labelled, with a rule-based fallback. The key comes from `~/jhc/secrets`, with a spend
  cap.
- **Clients:** fictional but recognizable. The mock Target is **Bullseye**; the others are Starbrew Coffee, Wellgreens,
  CVR, Wegford and Aldo. **FacilIT is real**, described as "Client portal manager".
- **People:** role names only. One login per role: `coord@`, `dispatch@`, `tech@`, `controller@` and `exec@ofs.com`.
  Outbound email is off, because ofs.com is a real domain.
- **The clock:** turnaround per step in the overview.
- **Delivery:** the app, the repo (jhcreative, private, Neale and Ann-Marie invited), the email with the deck
  (`opportunities/onefamilyservices-flows-and-views-2026-11-14.pdf`). Stretch: the narratives in an in-app help panel,
  unlisted on John's YouTube.

## Waiting on John (doesn't block the local build)

The box order and the OVH token, the GitHub repo create (`!` command in status), the Anthropic key, Neale's and
Ann-Marie's GitHub usernames, and the Cloudflare records. All are in `docs/status.md`.

## Canon written this session

- `jhc-agency/skills/product-ops/report-writer/references/flow-diagrams.md`: the flow decks, the application surface
  page, the key, happy path first.
- Team memories: happy path first; AG Grid for grids; the JHC apps box; the flow diagram canon.
