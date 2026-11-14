# Every defect found in the window, and what found it

Honest systems: we keep the defect list because it's the evidence the process works. Each was found before it
shipped. "Found by" names the check that caught it.

| # | Story | Defect | Found by | Fixed by |
|---|---|---|---|---|
| 1 | POC-02 (first) | A request-scoped session, where Tailor's rule needs function scope (ADR-0102) | Tailor's own session-scope test | Function-scoped session |
| 2 | POC-02 (first) | No Path P export hook: Tailor's portability suites failed (5 tests) | Tailor's own export round trips | `portability.py` |
| 3 | POC-02 (first) | Tailor's shared checkout moved under the session (another window) | The installer's version guard | A read-only archive of the right version; the other window left alone |
| 4 | POC-03 | Tailor's export codec can't carry `Decimal` or `date` | Reading the codec before modelling money | Money in integer cents, times as datetimes |
| 5 | POC-04 | The seed put 33 of 45 jobs over their client's cap (the plan says "a few") | Building the happy-path test: no draft was free of a rule | Most jobs under the cap; a test pins 3 to 12 |
| 6 | POC-04 | Two assertions of my own ended in `or True`: they couldn't fail | My own re-read before commit | Rewritten to check the real history |
| 7 | POC-05 | A socket waiting on its queue missed the client's close until the next ping | The gate's own run time: 326 s instead of about 25 | Watch for the disconnect too; a test pins it |
| 8 | POC-06 | 411 KB gzipped: every AG Grid module registered | Measuring the bundle | Five modules; the grid loads on demand; a budget in the gate |
| 9 | POC-06 | AG Grid error #200, a missing module | The e2e's console check | The module registered |
| 10 | POC-06 | The Paid tile said jobs were "waiting" | Jony, from the screenshot | No wait shown on Paid |
| 11 | POC-07 | The backend image lacked the Anthropic SDK | The stack failing to start | The lockfile generated from a clean environment |
| 12 | POC-07 | The TS generator made every defaulted field required | The typecheck | `--default-non-nullable=false` |
| 13 | POC-07 | The queue grid hid its overflow; the issue type showed its code; a superscript `$` in a label | Jony, from the screenshot | Narrower columns, labels, a plain label |
| 14 | POC-08 | A recommendation from 409 km away: the seed had no geography | Jony and Jen, from the screenshot | Techs based where sites cluster, licensed in neighbours |
| 15 | POC-08 | The login limit (per address) tripped by the e2e | The e2e | Per account and address, plus a looser per address |
| 16 | POC-08 | A test read a count before the list loaded | Running the e2e four times on fresh seeds | Wait for the count |
| 17 | POC-09 | The cap rule in office words on the phone; two stacked colons | Jony, from the screenshots | The rule in a tech's words; brackets |
| 18 | POC-10 | The suite used up the seed's ready jobs | The e2e: "no ready job" | Tests make their own |
| 19 | POC-10 | A sign-in per job tripped the login limit | The e2e | One session per account per worker |
| 20 | POC-10 | The Open total spilled out of its tile | Jony, from the screenshot | Tiles size to the amount |
| 21 to 40 | POC-11 | The cold review's 20 findings: one high (publish order), five medium, fourteen low | A fresh reviewer (DOD-3) | 17 fixed, 3 accepted: `docs/backlog/2026-11-14-cold-review.md` |
| 41 | POC-11 | The first cut of the write lock held it across the Claude call | My own re-read of my comment against the code | The call moved before the lock |
| 42 | POC-11 | I claimed 14 fixes had tests; it was 13 | Recounting before recording | The record and the unpushed commit corrected |

**The pattern worth telling a client:** four kinds of check found these.
- **The gate's own tests:** 1, 2, 4, 5, 7, 11, 12.
- **The browser e2e:** 9, 15, 16, 18, 19.
- **A person reading a screenshot:** 10, 13, 14, 17, 20.
- **A fresh reviewer:** 21 to 40.

Each kind caught things the others didn't.
