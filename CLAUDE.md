# Jahnel Group POC: JHC engagement

Engagement repo for **Jahnel Group POC** (prospect). Step 5 of John's Jahnel Group interview loop: the proof of
concept John builds from the client role play Ann-Marie Berdar ran in round 4 (2026-11-12). We run it exactly like a
new JHC client engagement: same skeleton, same gates, same paper trail. Current state lives in `docs/status.md`.

## Team OS

This repo carries engagement specifics only. Agents, policies, and shared skills live in the team operating
system: `~/jhc/jhc-agency`. Load `POLICIES.md` + your domain child file there at session start, per its
`CLAUDE.md`. Work about this engagement lives here, not there (D6).

## Engagement constraints (set by John, 2026-11-12)

- **Treat it as a client.** Folder structure, paths, docs, backlog and its own repo, like any JHC engagement
  (ADR `docs/adr/2026-11-12-run-the-poc-as-an-engagement.md`).
- **Two deliverables: the POC, and the record of how we built it.** John: "track every effort and deliver superb
  documentation of our process as well as POC itself in the repo." So the process docs (plans, ADRs, backlog,
  carry-forwards) are part of what Jahnel reads, and `history/` is not split out before they see it.
- **The client is a role play.** Facts about the client come from John's account of round 4 (`docs/meetings/`),
  never invented. Where we fill a gap with an assumption, the assumption is labeled as one.
- **Synthetic data only**, unless John says otherwise; built the way the podcast pipeline's `fixtures_gen` builds
  test episodes.

## Standing owners

| Area | Owner |
|---|---|
| Scope, acceptance criteria, this file | Angela |
| Calendar to the due date, carry-forwards | Anne |
| The client's voice (from the role play) | Nicola |
| Architecture, model calls, cost controls, the merge gate | Cesar |
| Backend and data | Pete |
| The screen | Nathan, with Jony on form |
| Synthetic data and the eval set | Jen |
| Privacy | Orly |
| The written recap and README | Lisa |
| Demo video, if the format calls for one | Henry |

## Calendar target (BP-1)

**Due Monday 2026-11-16** (John, 2026-11-12). Format and recipients to be confirmed by Neale, Jahnel's HR contact.

## Background

Interview prep, rehearsals and the cheat card live in `~/jhc/johnhiemstra/interview-prep/2026-10-jahnel/` (John's
own repo, PP-16). They are referenced here, not copied.

## Repo Map

```
docs/status.md       # The present tense: live, rollback, next, waiting on John
docs/carry-forward/  # Anne's session notes (PP-2)
docs/plans/          # Approved plans, one file each
docs/backlog/        # Backlog
docs/adr/            # Decision records (PP-5)
docs/releases/       # What shipped, per version
docs/meetings/       # Evidence as received (the round-4 account)
opportunities/       # Opportunities doc HTML + dated PDFs
proposals/           # jhc-proposal-jahnel-poc-<date>.pdf
history/             # Our process material (shown to Jahnel here; see constraints)
```
