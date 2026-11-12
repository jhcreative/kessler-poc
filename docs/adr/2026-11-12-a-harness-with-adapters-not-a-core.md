# 2026-11-12: A harness with adapters, not a vendor core

## Status
Accepted (John, 2026-11-12)

## Context
OneFamilyServices takes work in through Target's portal, Starbucks store emails, other clients' emails and
attachments, and FacilIT for smaller clients, and keeps its records in FieldDesk. Research (`docs/research/2026-11-12-facilit-deep.md`)
found FacilIT sells a full work-order-to-invoice system with a field app, approvals, billing and connectors, which OF
seems to use only as a connection. Options: (a) our own layer above every system; (b) FacilIT as the core, building
only what it can't do.

## Decision
We will build a harness: our own job record and rules, with an adapter for each way in and out (Target's portal,
email, FacilIT, FieldDesk, QuickBooks, Samsara). FacilIT is one adapter whose features we use where they serve, not
the core, because the largest clients set their own formats, and one format forced into another breaks on Target.

## Consequences
### Positive
- Every client's rules apply to every job, whatever door it came through.
- No client's format is forced into another's; a new client is a new adapter.
- No paid subscription becomes the thing we can't leave.

### Negative
- We own more: the job record, the rules, and each adapter.
- Features FacilIT already has (field app, signatures, approvals) need a decision per feature: use theirs through the
  adapter, or build our own.

### Risks
- If FacilIT's edition already covers most of it, the harness duplicates paid work. FI.1 (which edition) tests this.

## Positions
**John (product owner):** "I lean b but am seeing us building a harness that includes it rather than its the central
core - why? Target. Has its own way in and out of our system. Are we forcing one format in to another with this
notion of 'core'? also I dont like paid subscription dependencies in general"

**Angela (product owner, the team's PO):** "I lean (b) with some of (a): it's the buy-before-build lesson from runs 3
and 6, and Ann-Marie will likely notice it."

**Cesar (technical director), earlier the same day:** "A layer above all three is the only place one rule like
'Target: $25K without prior approval' can apply to every job however it came in. It also keeps the POC away from three
vendors' integrations."

## Participants
John (decision); Angela, Cesar, Simone (research); Pete (record).
