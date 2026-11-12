# 2026-11-12: Run the Jahnel POC as a JHC engagement

## Status
Accepted

## Context
Round 4 of John's Jahnel Group interview loop (2026-11-12) was a client role play with Ann-Marie Berdar. Step 5 is a
proof of concept built from that discovery. The work could have lived as a folder in John's interview prep. Jahnel
sells Subscription AI with a documented delivery process (Atlas: discovery, plan, build, validate, ship), so how
the POC gets built is as much on show as the POC.

## Decision
We will run the POC as a JHC prospect engagement in its own repo (`~/jhc/prospects/jahnel-poc`), with the standard
skeleton, gates and records, because the process record is a deliverable alongside the POC.

## Consequences
### Positive
- Every effort is tracked: plans, decisions, backlog, carry-forwards, releases.
- Jahnel sees how John works, not only what he built.

### Negative
- More paperwork on a short clock; Anne holds it to what the deliverable needs.
- `history/` would normally be split out before a client sees the repo; here it stays in.

### Risks
- If Jahnel wants only a demo, the process docs are reading they may skip; the README must lead with the POC.

## Positions
**John (product owner):** "the next step is the POC exercise - we're going [to] handle it just like another new jhc
client - same folder structure, same paths to work, docs, backlog, own repo - so lets set that up first so we can
track every effort and deliver superb documentation of our process as well as POC itself in the repo"

## Participants
John (decision); Angela (record); Cesar (scaffold).
