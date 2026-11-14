# POC-03: the job record (11:00 to 11:29)

**Goal (plan §5, §7):** the tables, the migrations, the states, and a synthetic seed of 45 jobs over every state,
each with a history in `job_events`.

## Built

- **`ofs/states.py`:** the state table everything shares (the seed, the tests, the commands):
  - 11 states and 16 commands, each with the roles that may issue it;
  - the happy path;
  - each state's queue from page 2.
- **`ofs/schemas.py`:** written first, as RTS-2 asks: the API contract in Pydantic (`CommandIn`, `EventEnvelope`,
  `JobOut`, `Refusal`).
- **`ofs/models.py`:** ten tables:
  - clients, contracts, sites, people, techs, fleet positions;
  - jobs, job events, invoices, and `qb_ledger` (the simulated QuickBooks).
  - Every value with a fixed list of options is also a database CHECK. Money is integer cents; times are UTC.
- **Typed end to end (John, mid-story):** every JSON column has its own Pydantic model, checked on every write:
  contract rules, approval, sign-off, invoice lines, and one payload model per command.
- **`ofs/seed.py`:** deterministic from a seed:
  - 8 clients (Bullseye, Starbrew Coffee, Wellgreens Pharmacy, CVR Pharmacy, Wegford Markets, Aldo Foods, Keystone
    Dental Group, Lehigh Valley Fitness); FacilIT is a channel, not a client;
  - 60 sites across PA, OH, NY, NJ, DE, WV and MD;
  - role-named people and 10 techs;
  - 45 jobs over all 11 states;
  - about 150 historical QuickBooks invoices.
  - Every job's history is a walk through the state table, checked step by step.

## Verified

- The gate went green with 20 tests on Postgres in 2.5 seconds: all 11 states on the board in the planned counts,
  every history legal and in time order, the three hard rails already true of the data, every aging bucket full, and
  the same seed giving the same world.
- `alembic check` joined the gate: the migration must match the models.

## Found

- **A JSON codec gap:** Tailor's export codec handles UUIDs and datetimes but not `Decimal` or `date`. Money became
  integer cents, and dates became timezone-aware datetimes. Exact, and simpler.

## Mineable

- **The one record, in code:** page 2's "one job record carries the contract guardrails" is `models.Job`, with parts
  A (identity), B (working fields), C (approval) and D (state), as John described them on 2026-11-12.
- **Synthetic data, deterministic:** every demo starts from the same world.
