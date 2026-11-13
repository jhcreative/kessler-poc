# Carry-forward 2026-11-13 18:27: the four-page blueprint, and the POC plan (Anne)

## State

Nothing live.
- The understanding is complete as four landscape pages:
  `opportunities/onefamilyservices-flows-and-views-2026-11-13.pdf`. The pages are current, recommended, improvement
  opportunities and application surface.
- Angela's POC plan is written and waits on John's approval (T3): `docs/plans/2026-11-13-poc-plan.md`. The walkthrough
  is `docs/plans/2026-11-13-poc-plan-walkthrough.md`.
- The backlog is filed as POC-01 to POC-16.
- **Due Monday 2026-11-16.** We are about a day behind the calendar, and the plan carries a cut line.

## Since the last note (15:47), in order

1. **Page 1 (current).** Job records shrank 10%. The by-hand blocks got more padding. A new arrow, Tony → Coordinators:
   "Tony tells the coordinators directly", because the record tells no one in real time.
2. **Pages 2 and 3 (recommended).**
   - Job records grew 10%.
   - Additional approvals moved above the "Updates the record" line, out of the main field.
   - The updates line then dropped to sit just above Dispatch and Onsite.
   - "Ways in" became "Incoming requests".
   - The key moved below the drawing, with the words under the icons.
3. **Page 4, Application Surface.**
   - Page 3 with the three views laid over it, a box tree with edges touching. The views are **1 Coordinator
     workspace**, **2 Dispatch and field app** and **3 Controller queue**.
   - The shading sits over the flow, so the flow fades back.
   - The labels are compact white boxes.
   - The intro names the numbered views.
   - The invoice gear moved into the controller queue.
4. **Canon.** The new rules are in `report-writer/references/flow-diagrams.md`: the fourth page; the key below with
   words under the icons; the lanes identical across pages.
5. **The plan.** John set the goals in his own words:
   - real-time visibility in all three views;
   - advancing work from any view;
   - one overview of every queue and state;
   - the detailed coordinator, dispatcher, tech and controller behaviors;
   - a realistic simulation;
   - structured data;
   - instant push;
   - Tailor pieces and the OVH patterns, with nothing reinvented.

   Angela turned those into acceptance criteria (G1–G3, C1–C3, D1–D3, T1–T4, B1–B3), an architecture (commands in,
   events out over a websocket, replay from `job_events`), the data model from the job-record draft, the simulation, the
   Tailor and OVH mapping, the calendar and the cut line, and a five-minute demo script.

## Records

- Deck: `opportunities/onefamilyservices-flows-and-views-2026-11-13.pdf`. Earlier versions are in `docs/flow/drafts/`.
  The source is `docs/flow/deck/understanding.py`.
- Plan, walkthrough, backlog: `docs/plans/2026-11-13-poc-plan.md`, `docs/plans/2026-11-13-poc-plan-walkthrough.md` and
  `docs/backlog/README.md`.
- What Cesar checked for the plan in Tailor:
  - FastAPI ships websockets (uvicorn with the `websockets` lock entry).
  - The backend runs one uvicorn process, so an in-process hub works.
  - Caddy's `reverse_proxy` passes WebSocket upgrades through.
  - Own-table modules have their own Alembic branch (ADR-0038, ADR-0040).
  - Multi-user auth exists (ADR-0026).
- Deploy: `ship-ovh-site.sh`, edge mode, `IMAGES=local`.

## Tradeoffs

- **Fresh VPS-1 recommended over the shared John-account box:** $5.75/mo buys a demo that never touches a client's site.
- **Rule-based intake drafting by default.** Claude only if John allows it (Q3). It's honest either way, because it's
  labelled.
- **The POC code lives in the instance, not in Tailor core**, because no client wants go into core. The seam is gap Q7.

## Lessons

- **A blueprint page turns a flow deck into a build plan.** Each view maps to a route, and each arrow maps to a command
  or an event.

## Next priority

John's walkthrough (Q1–Q11) and approval. Then Saturday morning: scaffold (POC-02), tables and seed (POC-03),
commands and tests (POC-04).

## Waiting on John

| Since | Item | Owner | Answer |
|---|---|---|---|
| 2026-11-12 | Neale's confirmation: the step-5 format, the recipients, what "deployed" means (Q6) | Anne | |
| 2026-11-12 | Remote org (Q8) | Cesar | |
| 2026-11-13 | Approve the POC plan, and the walkthrough Q1–Q11 | Angela | |
