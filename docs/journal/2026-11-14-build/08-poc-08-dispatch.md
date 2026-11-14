# POC-08: dispatch (13:18 to 13:39)

**Goal:**
- D1: approved jobs arrive.
- D2: each shows a recommended tech and the reasons.
- D3: dispatch approves the assignment.
- T4 came along.

## Built

- **`ofs/recommend.py`:** a pure function.
  - Hard filters: the skill, and a license in the site's state.
  - Then rank by straight-line distance from the truck, plus 40 km for each job already on the tech's board.
  - Every tech comes back, with reasons or with what they lack.
- **Endpoints:** `GET /api/jobs/{id}/recommendation` and `GET /api/techs`.
- **`/ops/dispatch`:**
  - Tabs: Ready, Needs review, On the board, Techs (a list; the map was a cut-line item).
  - The recommendation with four reasons, and Assign in one click.
  - An unqualified pick asks why, and the reason goes on record.
  - Needs review: reassign, ask the tech to wait, or return to dispatch.

## Verified

- **Jen's eval:** 20 cases whose answers were worked out by hand from a map before the code ran. Allentown to Trenton
  is about 73 km, and a job on the board counts as 40 km. All 20 passed on the first run.
- **Over HTTP:** every seeded ready job's top tech has the skill and the license, and says so.
- **The e2e:** D1 (a coordinator's approval lands in Ready within a second), D2, D3, the recorded override, and T4.

## Found

- **A 409 km recommendation,** from the first screenshot: the seed scattered techs and licenses with no geography.
  Techs are now based where sites cluster and licensed in their home state and its neighbours. The top recommendation
  is a median of 104 km and a 90th percentile of 266 km. John: "yeah its good with a couple of outliers liek that 💪".
- **The login limit tripped the e2e.** It now limits per account and address (10 a minute) and per address (60), so
  password guessing is still stopped without locking out an office behind one address.
- **Two e2e flakes,** found by running the suite four times on fresh seeds: a test read a count before the list loaded,
  and the limiter's memory carried over between back-to-back runs.

## Mineable

- **Recommended, with reasons, is the pitch for dispatch:** "Has the refrigeration skill · Licensed in NY · Truck T-06
  is 105 km away · Nothing else on the board". Transparent, not a black box.
- **Screenshot:** `docs/evidence/2026-11-14-poc-08-dispatch.png`.
