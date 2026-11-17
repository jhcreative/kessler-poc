# Plan: the final presentation (Angela)

| Field | Value |
|---|---|
| Status | Approved shape, John, 2026-11-16. The pages are built one at a time with John, page 1 first |
| Story | POC-16 (the email and the deck) and POC-17 (the video) |
| Due | Monday 2026-11-16 (BP-1) |
| Recipients | Neale and Ann-Marie. John sends; nothing is sent by an agent |
| Message | Efficiencies that add up, measured by Cost of Delay (John, 2026-11-13), arriving at one centralized record |

## 1. What we deliver

| # | Item | Done when |
|---|---|---|
| D1 | **The email:** a short text intro, with the repo, the live app and the YouTube demo linked, and the PDF attached. Written as a text file John pastes: `docs/delivery/2026-11-16-email.md` | Lisa's edit is in (RTP-3); every link opens; John has it |
| D2 | **The logins email:** the passwords only, sent separately from D1 | The five passwords match `box-apps-demo-logins.env`; John has it |
| D3 | **The PDF:** nine landscape pages, text and graphic alternating, the same three links on page 9 (§2) | Rendered from source; every page passes §4; links click in the PDF |
| D4 | **The demo video:** one, 3 to 4 minutes, a single request through the five views, recorded from the Playwright e2e, captioned, no voice. Uploaded **unlisted** by John to his channel | The URL plays signed out; it's in D1 and D3 |

## 2. The pages (John, 2026-11-16)

All landscape, 11 × 8.5 (Q1). Text pages run in two columns.

| Page | Kind | Content | Done when |
|---|---|---|---|
| 1 | Text | What we did: we mapped the system, then found where it can improve | John approves the page |
| 2 | Graphic | **Current Request Flow**, redrawn | John approves the page |
| 3 | Text | The thesis: a centralized system is what serves the company best | John approves the page |
| 4 | Graphic | **Recommended Request Flow**, redrawn, QuickBooks outside | John approves the page |
| 5 | Text | Small sub-systems improved on the way to the center, with the opportunities table (§3) | John approves the page; Jen has checked every number |
| 6 | Graphic | **Flow Improvement Opportunities**, redrawn, gears numbered to the table | Every gear number matches a row on page 5 |
| 7 | Text | The application concept, including the turnaround clock in the overview (it measures the efficiencies) | John approves the page; Cesar has checked the technical claims |
| 8 | Graphic | **Application Surface**, redrawn: five views; the three inputs and the two exports outside | The views match the live app |
| 9 | Text | Summary: the links (repo, live app, video) and how to sign in as each of the five roles, emails only | Every link opens; each login email signs in on the live site |

### Drawing rules for the redraw

- **Inputs and exports sit outside the app surface** on page 8 (John, 2026-11-16). Inputs: Target portal, Emails,
  FacilIT. Exports: QuickBooks, and the invoice delivered in each client's own format. They appear the same way on
  pages 4 and 6, so the three recommended drawings agree.
- **Five views** on page 8 (Q2): Coordinator, Dispatch, Tech, Controller, with Overview as a frame around them.
- **The gears are numbered** in flow order, left to right, the same numbers on pages 6 and 8. The three input gears
  share number 1.
- Gear numbers are the only new marks; the flow-diagram canon holds otherwise
  (jhc-agency `skills/product-ops/report-writer/references/flow-diagrams.md`).

## 3. The opportunities table (page 5)

Columns: **#, Opportunity, Priority, Impact** (John, 2026-11-16). A small mark beside the number says the POC proves it
(Q5).

- **Priority** is one of three (John, 2026-11-16): **Immediate**, **Short term**, **Long term**. Immediate and short
  term are what can be done first without building the whole system. **Long term is the whole centralized app** and
  the efficiencies that result.
- **Impact** is mostly hours saved (an estimate) and the Cost of Delay reduced. We draft each from the round-4 facts,
  labelled as an estimate, with its assumption in a footnote; John adjusts; Jen checks the arithmetic (Q3).

| # | Opportunity | Proven in the POC | Priority (draft, settled at page 5) |
|---|---|---|---|
| 1 | Job records drafted automatically from each source (portal, email, FacilIT) | Yes | Immediate |
| 2 | Contract guardrails checked before work is assigned | Yes | Short term |
| 3 | A recommended tech at dispatch, with the reasons | Yes | Short term |
| 4 | Updates flow one way, so everyone sees the same record | Yes | Long term |
| 5 | Closed work pushed to the billing queue automatically | Yes | Short term |
| 6 | Invoices drafted automatically in each client's format (an export) | Yes | Immediate |
| 7 | Export to QuickBooks | Yes (simulated) | Immediate |

Facts the estimates draw on (`docs/meetings/2026-11-12-round-4-discovery.md`): 20,000 requests a quarter, three
intake people, $80K–$200K a year written off in disputes, QuickBooks and a few spreadsheets as the billing system.

## 4. Gates, every page

| Gate | Owner | Check |
|---|---|---|
| Evidence | Angela, Jen | Each claim maps to the mining guide's "What we can claim today"; nothing from "can't claim yet" |
| Synthetic said | Angela | Synthetic clients and data, simulated QuickBooks and fleet, labelled where they appear |
| Form | Jony | Matches the flow-diagram canon and the JHC brand sheet; no runts (PQ-5e), no UI dashes (PQ-34) |
| Words | Lisa | RTP-3 on every page and both emails; no hedging (PQ-5b), no trailing prepositions (PQ-5c) |
| Client's voice | Nicola | Pages 1, 3, 5 and 7 answer what Ann-Marie asked in round 4 |

## 5. Dependencies

| What | Owner | Blocks |
|---|---|---|
| Neale's and Ann-Marie's GitHub usernames, for the invites | John | The repo link working for them (D1, D3 page 9) |
| The video uploaded unlisted, and its URL | Henry, then John | D1, D3 page 9 |
| The reseed before the screenshots (clears request 1046) | John's go | Page 8's check against the live app; the video, if recorded on the box |

## 6. Decisions (John, 2026-11-16)

| # | Decision |
|---|---|
| Q1 | All nine pages landscape |
| Q2 | One video, 3 to 4 minutes, from the e2e, captioned, unlisted |
| Q3 | Login emails in the PDF; passwords in a separate email |
| Q4 | The email is a text file John pastes |
| Q5 | Redraw the graphics: numbered gears that track to a table on a text page; the three inputs and the QuickBooks export outside the app surface |
| R1 | Recommended tech and QuickBooks export get gears (6, 7); the clock goes on page 7, not the table |
| R2 | Page 8 shows five views, not three |
| R3 | We draft the impact estimates; John adjusts |
| R4 | Priority: immediate, short term, long term; long term is the whole centralized app |
| R5 | The table marks what the POC proves |
| R6 | The client-format invoice is an export, outside the app surface, like QuickBooks |
| R7 | Gears renumbered (2026-11-17): recommended tech 6 → 3, updates 3 → 4, push to billing 4 → 5, invoices 5 → 6 |
| R8 | The end of the flow (2026-11-17): invoicing drafts and exports to client systems and QuickBooks; QuickBooks comes first and feeds both collections (the final phase) and the company's accounting |
| R9 | Page 10 (2026-11-17): the demo passwords, unbranded, in a TEST copy only (`assemble.py --with-logins`, gitignored); out of the final version |
| R10 | Page 6 (2026-11-17): no dek; rows 4, 5, 6 and 7 are long term, since each needs the centralized record. Immediate: 2, 8, 9. Short term: 1, 3 |
| R11 | Pages 1, 3 and 5 (2026-11-17): "five work on their own today; four arrive with the shared record"; pages 1 and 3 in two columns, the text block left, the sections right |
