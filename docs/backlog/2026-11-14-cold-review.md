# Cold review, 2026-11-14 (POC-11, DOD-3)

**The reviewer:** a fresh agent, given the code and what the app is for, not our conclusions. It reviewed in DOD-3's
order: tests, then code, then security. It ran the gate (green at `9d29152`) and changed nothing.

**The result:** 20 findings. 17 are fixed, 13 of them with a test (the row-lock test proven to fail without its fix). 3 are accepted, with
the reason. "Test" names the file that pins it.

| # | Sev | Finding | Disposition |
|---|---|---|---|
| 1 | High | Event ids are assigned at flush, not commit. Two commands in flight could publish out of id order, and a view would drop the lower id as already sent | **Fixed.** One writer at a time (`hub.WRITE_LOCK`): write, commit, publish, then let go, so id, commit and publish order are one order. It holds for one uvicorn process (plan §4). The Claude call stays outside the lock. No dedicated test: it's true by construction |
| 2 | Med | A tech's replay is filtered by who holds the job now, so a job reassigned away while they were offline stays on their phone | **Fixed.** The phone reloads its short list after a drop (`useLive` `reloadOnReconnect`). Not automated: it needs an offline browser |
| 3 | Med | The issue type and estimate could change after dispatch, around the approval rail. A raised estimate kept the old approval. A tech could change the issue type | **Fixed.** Both fields are the coordinator's, and fixed once dispatched. Raising the estimate voids the approval. Test: `test_review_fixes.py` |
| 4 | Med | `TRUSTED_PROXY` defaults to loopback. If the box doesn't set the edge's address, everyone shares one login limit | **Guarded.** `ship.sh` refuses a box `.env` without `TRUSTED_PROXY=10.240.0.2/32` (and `COOKIE_SECURE=1`) |
| 5 | Med | The socket re-checked the login only when idle | **Fixed.** It re-checks every 25 s, busy or idle. The idle case is tested (`test_ws.py`); the busy case isn't |
| 6 | Med (test) | The seed approved invoices that failed their check, and the rail test couldn't fail | **Fixed.** The seed's checks come from the backend's own `invoice_check`, and it refuses to approve a failed one. Test: every seeded invoice carries the backend's check |
| 7 | Med (test) | No test of the row lock: removing it left the suite green | **Fixed.** Two real sessions race one job; the second waits, then is stale. **Proven to fail with the lock removed** |
| 8 | Low (test) | The wrong-state test asserted only `not_allowed` | **Fixed.** It asserts the 409 and the reason |
| 9 | Low (test) | Publish-after-commit was untested, and the tech replay test could pass with nothing to check | **Fixed.** A commit that fails publishes nothing (test). The replay test asserts it has jobs |
| 10 | Low | The QuickBooks document number (`max + 1`) could collide under two approvals | **Fixed** by #1: it's computed inside the write lock |
| 11 | Low | A password over 72 bytes made a 500; bcrypt blocked the event loop | **Fixed.** It's a 401, and bcrypt runs in a thread. Test: the long password |
| 12 | Low | Frames buffered while the list loaded ignored the view's scope | **Fixed.** Test: `store.test.ts` |
| 13 | Low | A tech login without a tech record would see every unassigned job (`IS NULL`) | **Fixed.** It sees nothing. Test |
| 14 | Low | The login limiter's memory grew without bound | **Fixed.** Empty keys are pruned past 10,000. Not tested |
| 15 | Low | New request had no throttle; the job lists run 4 queries per job | **Fixed:** one per person every 3 s (test). **Accepted:** the per-job queries, at demo scale. Exec keeps New request on purpose: it's the demo controls |
| 16 | Low | Only three Claude exceptions fell back; anything else was a 500 | **Fixed.** Any failure falls back, labelled. Test |
| 17 | Low (test) | The Secure-cookie test set the value it checked; the logout test cleared the cookie itself | **Fixed.** The default is tested with the variable unset, and logout is tested by the server's own expiry header |
| 18 | Low | Trucks were seeded at home even for techs on site | **Fixed.** Test |
| 19 | Low | The tie-break sorted "Tech 10" before "Tech 2" | **Fixed:** natural order |
| 20 | Low | `/api/health` is unauthenticated and shows counts | **Accepted.** The counts are of synthetic data, and the deploy's live check reads them |

**Evidence after the fixes:**
- The gate: 114 passed, vitest 7.
- The e2e: 12 passed, twice in a row.
- `check-live.py`: 7 of 7, with the event in 1.7 s.

**Found while fixing:**
- The first cut of #1 held the write lock across the 2 to 4 s Claude call. Caught before commit: the call now runs
  first.
- The new throttle (#15) made the coordinator e2e's first click wait. The test now waits and retries, as a person
  would.
