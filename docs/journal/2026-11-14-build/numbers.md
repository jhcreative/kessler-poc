# The numbers (measured, with where each comes from)

## Time

| What | Number | Source |
|---|---|---|
| The window | about 10:00 to 15:29 Eastern, Saturday 2026-11-14 | commit times |
| Plan approved to every view built | about 4.5 hours (10:00 to 14:34) | commits `e42c951` to `77248a3` |
| The Tailor-parts decision | under 30 minutes, from John's question to the lean skeleton | the timeline |

## Size of what was built (`app/` at `aa8594a`)

| What | Number |
|---|---|
| Files tracked under `app/` | 98 |
| Backend application code | 2,701 non-blank lines in 17 files |
| Backend tests | 1,176 lines; 114 tests collected |
| Frontend, hand-written | 1,886 lines, plus 191 of CSS |
| Frontend, generated from the backend (types) | 1,385 lines |
| Browser e2e | 401 lines, 12 tests |
| Migrations | 2 |
| Frontend packages (dev included) | 102 |
| Backend runtime pins | 35 |
| Against: the Tailor instance it replaced | 1,441 files, about 117,000 lines |

## Quality gates (last run, `c41d5c5`, same `app/` tree as `aa8594a`)

| Gate | Result |
|---|---|
| Backend pytest on Postgres | 114 passed, about 46 s |
| Frontend unit tests (vitest) | 7 passed |
| Types in step with the backend | yes |
| Browser e2e (Playwright, real Chromium, the real stack) | 12 passed, run twice after the fixes |
| `check-live.py`, locally | 7 of 7 |
| `ship.sh --dry-run` | green |
| `npm audit`, `pip-audit` | 0 known vulnerabilities |
| The cold review | 20 findings: 17 fixed, 3 accepted |
| The recommendation eval | 20 of 20 hand-checked cases |
| The rules fallback eval | 60 of 60 synthetic requests, every field exact |

## Speed

| What | Number | Where |
|---|---|---|
| A change reaching another open view (G1) | 21 ms | local stack, POC-05 |
| A new request reaching an open socket, Claude's drafting included | 1.7 to 2.6 s | `check-live.py`, local |
| A Claude draft | 2 to 3.5 s | two live calls, POC-07 |
| Every e2e "within a second" check | passed at 1,000 ms | the e2e |

## Size on the wire (gzipped)

| Chunk | Size | Budget |
|---|---|---|
| Sign-in entry | 91 KB | 100 KB |
| The grid (AG Grid Community, shared) | 232 KB | 250 KB |
| Each view | under 4 KB | 250 KB |

## Cost

| What | Number |
|---|---|
| A Claude draft | about 1,000 tokens in and 80 out; about half a cent at $4 and $20 per million |
| An hour of demo at one request every 45 s | about $0.45 |
| In-app cap | 300 drafts a day, on top of the account's spend cap |

## The synthetic world (seed 1114)

8 clients, 60 sites in 7 states, 16 people (role names), 10 techs, 45 jobs over 11 states, about 150 historical
QuickBooks invoices across every aging bucket. The top recommendation's distance: median 104 km, 90th percentile
266 km.
