# POC-09: the tech's phone (13:39 to 14:16)

**Goal:**
- T1: the tech sees only their own jobs, and new jobs arrive.
- T2: complete a job (arrive, work, sign-off, close).
- T3: needs review shows at once to dispatch and the coordinator.

## Built

- **`/ops/tech`:** My schedule.
  - The tech's own jobs only. The server filters them, and the live store keeps to the tech's own id, so a job
    reassigned away leaves.
  - Hand-rolled (no grid on a phone, per the AG Grid ADR) and phone first, with 44 px and larger targets.
- **`/ops/tech/:job`:**
  - the street address and the site contact;
  - the rules in a tech's words ("If the work will run over $25,000, send it for review: the client approves first");
  - Arrive, then the work fields (parts, part numbers, hours on site);
  - Close: the site signed off, or nobody could sign and why;
  - Needs review: a reason and one line for dispatch.

## Verified

The e2e at 390 by 844 px with touch passed both new tests on their first run:
- **T1:** dispatch assigns elsewhere, and the job is on the phone within a second.
- **T2:** the tech arrives, logs a special-order part and closes with a sign-off. The office's API then reads billing
  review, the sign-off and the part number. One record.
- **T3:** needs review from the field raises dispatch's count in an open desk browser within a second.

## Found

- **Jony, from the phone screenshots:** the contract cap read like office language, so it now tells the tech what to
  do; and the waiting line stacked two colons.

## Mineable

- **The one record, end to end, in a single screenshot:** the phone's job is the one the coordinator's test pushed
  over the cap and got approved, and it reaches the tech saying "Client approved, ref APR-7731".
- **Screenshots:** `docs/evidence/2026-11-14-poc-09-tech-schedule.png` and `…-tech-job.png`.
