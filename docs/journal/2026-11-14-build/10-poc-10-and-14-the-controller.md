# POC-10 and POC-14: the controller (14:16 to 14:34)

**Goal:**
- B1: closed jobs land in the billing queue.
- B2: approve the drafted invoice, and it auto-submits to QuickBooks (simulated).
- B3: the aging summary (POC-14, below the line).

## Built

- **Endpoints:** `GET /api/jobs/{id}/invoice` (lines, total, the client's format, the check) and `GET /api/qb/aging`
  (open invoices from `qb_ledger` by days past due: Current, 1 to 30, 31 to 60, 61 to 90, Over 90).
- **`/ops/controller`:**
  - aging pinned across the top, labelled QuickBooks (simulated), live;
  - Billing review, Sent back, Submitted, Paid;
  - the invoice with its check in words, and Approve and submit, disabled with the reason when the check failed (the
    backend refuses it anyway);
  - Send back with a reason;
  - the QuickBooks document number once submitted.
- **The loop closed:** the coordinator can redraft a sent-back invoice.

## Verified

The e2e covered:
- **N3:** a tech closes a job, and it lands with its invoice within a second. Approval submits it as "QB-…", and the
  Current aging counts one more.
- **The failed-check branch:** no sign-off, so no approval; sent back; redrafted.
- **Over HTTP:** every open invoice falls in exactly one bucket.

## Found

- **The suite used up the seed's ready jobs:** tests now make their own through the API.
- **Per-job sign-ins tripped the login limit:** each test worker now keeps one session per account, as a person
  stays signed in.
- **Jony:** the Open total spilled out of its tile.

## Mineable

- **Page 3's auto-drafted invoice gear is real:** drafted at close, checked before approval, submitted on one click.
- **Screenshot:** `docs/evidence/2026-11-14-poc-10-controller.png`.
