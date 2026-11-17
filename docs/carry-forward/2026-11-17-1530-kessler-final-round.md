# Carry-forward 2026-11-17 15:30: Kessler at kfs, v0.1.4 live, the deck final, the README (Anne)

## State

- **Live:** https://kfs.apps.johnhiemstra.com, images `ed7e009` (v0.1.4). `check-live.py`: 7 of 7. Demo data
  reseeded after the check: 45 jobs, 15 invoices. Five `@kfs.com` logins, one shared password, in
  `~/jhc/secrets/jahnel-poc/box-apps-demo-logins.env` and on page 9 of the PDF. ofs.apps no longer answers.
- **Rollback:** OVH snapshot `655c53df` (2026-11-17 20:06 UTC, v0.1.3), or `ship.sh --rollback b2f4949` for the
  images alone. John's (OPS-5).
- **The deck:** `docs/flow/kessler-poc-final.pdf`, nine pages, gitignored (page 9 carries the passwords, filled at
  render time from the secrets store). Source: `docs/flow/final/` (hand-edited text pages 1, 3, 6, 7, 9; graphic
  pages 2, 4, 5, 8 from `graphics.py`). `python3 docs/flow/final/assemble.py` rebuilds it in seconds.
- **The video:** https://youtu.be/_qfYcEbQ92o, unlisted, uploaded by John. The open card no longer names Jahnel Group
  (re-rendered from take 2; the YouTube copy still has the old card until John re-uploads).
- **The README:** rewritten at the root for a reader new to the repo (Jony, Nathan; Lisa's pass in).

## Releases this round

| Version | Images | What | Go |
|---|---|---|---|
| v0.1.2 | `733887b` | Kessler Facility Services; the domain moved to kfs; `@kfs.com` logins, one shared password | John's `! ship.sh` |
| v0.1.3 | `b2f4949` | Dispatch "On the board" after "Techs" crashed; Show password and paste cleanup on sign-in | "redeploy without me" |
| v0.1.4 | `ed7e009` | The login title without "ops" | "go" |

## Revisions to the deck (John's hand passes, the agents' fixes)

- Page 1 two columns: all of John's paragraphs in the left column at a smaller size, the sections in the right.
- Page 3, John's rewrite: FieldDesk and FacilIT as paid services; the case for building the single source of truth
  in house.
- Page 6: "Opportunity by effort & impact"; group lines rewritten by John.
- Page 7: retitled "POC Application Design", with John's rewrites in the dek and the sections.
- Page 9: "Proof of Concept"; "Read. Watch. Use."; the YouTube link filled; the logins as "Live application logins by
  role".
- Typos fixed at John's ask: OPPORTUNITIES (p1), the current system, etc., a third-party (p3), components. (p6),
  the the (p7).
- The email: the YouTube link in; "no sound" dropped (the video has music now).

## Observations

1. **A paste from a PDF is not the password.** Coord's first live sign-ins were 401s with the right password: a
   masked field hides a trailing space or a typographic dash. The demo logins went out on paper, so the sign-in form
   has to forgive the paste. v0.1.3 cleans it and shows the password on request. Worth carrying into Tailor's sign-in.
2. **Two grids in one React slot are one grid.** Conditional siblings of the same component type reuse the instance;
   AG Grid then formats one tab's rows with the other tab's columns. Key every conditional grid. The e2e never
   switched tabs in that order; it does now, both ways.
3. **The live check reseed is part of the ship.** `check-live.py` adds job 1046, so every ship ends with a reseed
   before John tests. It ran after each of the three ships.
4. **One snapshot slot means each ship replaces the last restore point.** `66cf4cb3` (pre-rename) is gone; the oldest
   restore point is now v0.1.3.
5. **Hand edits and generated pages share a folder.** `assemble.py` renders whatever is on disk and never writes the
   text pages (PP-11). John's edits to the graphic pages (4, 5) would be lost if `graphics.py` ran again; it wasn't
   run this round.
6. **Coverage is now measured, not claimed.** Backend 92% line and branch (`app/scripts/coverage.sh`, coverage.py
   added to the dev requirements). The frontend's screens are covered by the 15 browser tests, not by a line count.

## Naming

John: "change naming from jahnel-xxx to kessler-xxx everywhere in repo". Done for every file and file name inside
the repo (`kessler-poc-final.pdf`, `kessler-poc-understanding.pdf`, the captions, the proposal prefix). The names that
live outside the repo wait on John: the GitHub repo `jhcreative/jahnel-poc`, the folder `~/jhc/prospects/jahnel-poc`
and the secrets folder `~/jhc/secrets/jahnel-poc`. "Jahnel Group" as the company we built this for stays in the
engagement record (`CLAUDE.md`, the meetings).

## Waiting on John

- The outside names above.
- Re-upload the video with the new open card, or keep the current upload.
- Neale's and Ann-Marie's GitHub usernames, for the repo invites.
- The email: addressee, and whether to keep its two labels.
