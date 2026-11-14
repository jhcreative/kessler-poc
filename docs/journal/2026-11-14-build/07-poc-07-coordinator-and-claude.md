# POC-07: the coordinator workspace, and Claude drafting intake (12:22 to 13:18)

**Goal:** C1 (all, mine, a single job), C2 (drafts from source, reviewed and approved for dispatch). C3, from POC-13,
came along.

## Built

- **`ofs/intake.py`:** Claude drafts a job from the request as it arrived.
  - **The model:** chosen at build time, as the plan said, after loading the `claude-api` skill: `claude-opus-5-5` at
    low effort, structured output into a typed model, server-side refusal fallbacks on, SDK `anthropic==2.3.0`.
  - **The fallback:** the rules draft instead, labelled with the reason, when there's no key, the daily cap (300) is
    reached, the call fails, Claude declines, or the draft names a client or store we don't have.
  - **The record:** the model and its tokens go on the job's event.
  - **The key** reaches the container at runtime from `~/jhc/secrets` (John: "use same key for demo purposes"). It's
    never in the repo or an image.
- **`ofs/sources.py`:** synthetic requests in three shapes: a client portal record, a store email, a FacilIT ticket.
- **`/ops/coordinator`:**
  - Queues: Drafts, Mine, Needs approval, Needs review, All.
  - The job record:
    - identity, read-only;
    - "The request as it arrived";
    - the working fields (only changes are sent);
    - the approval rule in its own words, and the record-approval form;
    - the contract panel;
    - the history, newest first.
  - The actions sit on the record's pinned title row. Saves show the PQ-14 toast.

## Verified

- **Two live calls, both drafts exact:** about 1,000 tokens in and 77 out, 2 to 3.5 seconds each. At $4 and $20 per
  million tokens, that's about half a cent a draft.
- **The gate never calls the model,** but its tests do check:
  - the rules reading 60 synthetic requests in every shape, every field exact;
  - each fallback reason.
- **The e2e, N1 and N1b in a real browser,** with a live Claude draft:
  - New request, check against the request, qualify;
  - push the estimate over the cap, see the rule block dispatch;
  - request and record the client's approval (APR-7731), then dispatch;
  - the dispatcher assigns from another session, and the coordinator's open record shows Assigned within a second.

## Found

- **The SDK was missing from the backend image:** its lockfile is now generated from a clean environment.
- **The TypeScript generator** made every field with a default required, so it now runs with
  `--default-non-nullable=false`.
- **Two test faults of mine:** a label pattern, and a hard-coded job count.
- **Jony, from the screenshot:** the queue grid hid its overflow, the issue type showed its code ("plumbing"), and a
  superscript `$` sat in a label.

## Decided

- **The ADR:** `docs/adr/2026-11-14-claude-drafts-intake.md`.
- **The model:** the plan's first thought was a Sonnet-class model. The skill's rule is Opus 5.5 unless John names
  another. Switching is one line, and at this volume the difference is cents.

## Mineable

- **Page 3's "draft from source" gear is real:** the draft says who wrote it, and the coordinator checks it against
  the original before anything moves.
- **Screenshot:** `docs/evidence/2026-11-14-poc-07-coordinator.png`.
