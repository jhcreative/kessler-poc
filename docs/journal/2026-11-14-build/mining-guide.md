# Mining guide: from this journal to client-facing documents

For the session that writes the README (POC-16), the recap email to Neale and Ann-Marie (Lisa, RTP-3), the narration
for the Playwright videos (POC-17, Henry), or a case study. Read this file first, then the story files it points to.

## The rules for anything client-facing

- **Every claim needs its evidence** (V-1, PQ-5). Each line below names its source. If there's no source, don't say
  it.
- **Say what's synthetic:** clients are fictional but recognizable (Bullseye, Starbrew Coffee and the rest), people are
  role names, QuickBooks and the fleet are simulated, and the costs and turnaround times come from synthetic
  histories. FacilIT is a real product, described as "Client portal manager".
- **John's words stay as he wrote them** (ST-10). Quote him exactly or not at all.
- **No hedging, and no maxims** (PQ-5b). Lead with the efficiency, measured: the message is "efficiencies that add up,
  measured by Cost of Delay", not "a new master system".
- **In public posts** (LinkedIn), the dev agents go by their le Carré aliases. The studio keeps its names. Jahnel's
  private repo and email can use the team's names.
- **Lisa edits** the email and the README before John sends anything (RTP-3).

## What we can claim today, with the evidence

| Claim | Evidence |
|---|---|
| One job record carries the contract's guardrails; every view updates it, and it tells every view | `03-…`, `04-…`; `app/backend/ofs/commands.py` |
| A change made in one view shows in every other open view within a second, with no reload (G1) | e2e: `overview.spec.ts`, `coordinator.spec.ts`, `dispatch.spec.ts`, `tech.spec.ts`; 21 ms measured locally |
| A view that drops its connection catches up on what it missed, with nothing twice | `test_ws.py`, the replay test |
| A request is drafted from its source by Claude, labelled, and checked by a person before anything moves (page 3's first gear) | `07-…`; two exact live drafts; the e2e with a live draft |
| If Claude can't draft it, the rules do, and the job says why | `test_intake.py`; 60 of 60 rule drafts exact |
| The contract rule holds dispatch until the client's approval is on record, in its own words | `test_commands.py`; `coordinator.spec.ts` |
| Dispatch gets a recommended tech with its reasons (skill, license, distance, load) | `08-…`; 20 of 20 hand-checked cases |
| The tech's phone shows only their jobs; a job closed in the field reaches billing with its invoice drafted | `09-…`, `10-…`; `tech.spec.ts`, `controller.spec.ts` |
| An invoice that fails its check can't be approved; one that passes is submitted to QuickBooks (simulated) in one click, and the aging moves | `10-…`; `controller.spec.ts` |
| The turnaround of each step comes from the record's own history (the Cost of Delay view) | `06-…`; `/api/overview` |
| Built with tests at every layer and a fresh reviewer's audit, which found and fixed a real ordering bug | `defects.md`; `docs/backlog/2026-11-14-cold-review.md` |
| Typed end to end: the screens use types generated from the backend, and the build fails if they drift | `06-…`; `app/scripts/types.sh` |
| Small and owned: about 4,600 hand-written lines; dependencies pinned and audited with 0 known vulnerabilities | `numbers.md` |

## What we can't claim yet

| Not yet | Why | When it can be said |
|---|---|---|
| "Deployed", "live at ofs.apps.johnhiemstra.com" | The box isn't ordered | After `ship.sh --first`, with `check-live.py` passing against the real URL |
| Real-time "across the internet", or R1 retired | Only proven locally | `check-live.py`'s R1 lines passing on the box |
| New requests arriving on their own, trucks moving, the demo controls | POC-15 isn't built | After POC-15 |
| Anything about load, scale or many users | Not tested, deliberately (the test strategy) | Not for this POC |
| Real QuickBooks, Samsara, FacilIT or portal integration | Simulated by design | That's the next engagement, not this one |
| Any measured saving for OneFamilyServices | No real data | Only with their data |

## Where each document's material lives

**The README** (POC-16): what it proves, how to run it, and the four pages mapped to the code.
- *What it proves:* the plan's §1 and §2, plus "What we can claim today" above.
- *Run it:* `app/.env.example`, `app/scripts/init-env.sh`, `docker compose up`, `python -m ofs.seed`,
  `python -m ofs.logins`; the gate is `app/scripts/gate.sh`; the e2e is `app/scripts/e2e.sh`.
- *The four pages to the code:*
  - page 1 (the problem): `docs/flow/`;
  - page 2 (one record): `ofs/models.py`, `ofs/states.py`, `ofs/commands.py`;
  - page 3 (the gears): `ofs/intake.py` (draft from source), the rails in `commands.py` (guardrails before work),
    `ofs/hub.py` and `ofs/ws.py` (one-way updates), `ofs/recommend.py` (the push to the queue), `_draft_invoice` and
    `invoice_check` (the auto-drafted invoice);
  - page 4 (the surface): `frontend/src/routes/` (Coordinator, Dispatch, Tech, Controller, Overview).
- *How it was built:* this journal, `02-…` first.

**The recap email** (Lisa, short): the deck is attached. Three facts with evidence (one record and live views; Claude
drafting with a human check; contract rules enforced), the URL, the repo invite, and the logins (sent separately, not
in the email body).

**The Playwright narratives** (POC-17): the e2e already performs each scene. Record them; don't write new flows.

| Narrative | Scene | The e2e that already does it |
|---|---|---|
| N1 | The coordinator | `coordinator.spec.ts`: draft, qualify, dispatch, moves on live |
| N1b | Over the cap | the same test: the rule, the approval, dispatch |
| N2 | Dispatch and onsite | `dispatch.spec.ts` test 1, then `tech.spec.ts` test 1 |
| N2b | Needs review | `tech.spec.ts` test 2, then `dispatch.spec.ts` test 3 |
| N3 | The controller | `controller.spec.ts` test 1 |
| N4 | The overview | `overview.spec.ts` test 2 |

**A case study, or Jahnel's read of the process:** `02-…` (we measured, then cut a platform we didn't need), `11-…`
(we asked a fresh reader to find what we missed), `defects.md` (four kinds of check, each finding what the others
missed), `decisions.md` (the product owner's calls, in his words, each recorded where it governs).

## Screenshots, all synthetic data

`docs/evidence/2026-11-14-poc-06-overview.png`, `…-poc-07-coordinator.png`, `…-poc-08-dispatch.png`,
`…-poc-09-tech-schedule.png`, `…-poc-09-tech-job.png`, `…-poc-10-controller.png`. Retake them on the box for anything
that says "deployed".
