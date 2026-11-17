# Decisions in the window, in John's words (ST-10: quoted as written)

| When (about) | Decision | John's words | Recorded in |
|---|---|---|---|
| 10:00 | Start the build from the handoff: the sprint-start checks, then POC-02 | "Angela have team resume the Jahnel POC build … follow its "Start here" steps: the sprint-start checks, then POC-02." | `docs/backlog/2026-11-14-sprint-start.md` |
| 11:18 | The demo's intake drafting uses the existing Anthropic key | "use same key for demo purposes" | `docs/status.md` |
| 11:20 | Go on POC-03 | "go ahead with POC-03 - what is localhost url?" | the timeline |
| 11:22 | Build from Tailor's parts, not as a Tailor site | "oh - i thought we'd just use parts of Tailor - do we really think its suited ot framerwork for app like this?" · "I mean the whole publihsing thing is crift" · "we dont publihs pages, we handle data" · "we dont care about AEO/SEo" · "etc" | `docs/adr/2026-11-14-tailor-parts-not-a-tailor-site.md` |
| 11:23 | Admin is users, integrations and config only; work happens per role in the frontend | "yeah 'admin' for this would be just users/integrations/config. the frontend is where work gets done for eaxch role" | the same ADR; agency ADR-0014 |
| 11:24 | Save it as the base for future apps (not Tailor web, ecom or blog) | "Anne Cesar save this pattern as future base for liek apps" · "that are not Tailor web/ecom/blog but actual apps liek this POC" | agency ADR-0014, TEAM-11, the team memory |
| 11:26 | Strongly typed, with TypeScript models that correspond | "so we have strongly typed data strcutures readable in codebase?" · "or we will have" · "ok great w ewill want them to correspond to Typescript models for front end" · "i know its our usual but want to reinforce here" | ADR-0014's Types row; `app/scripts/types.sh` |
| 11:28 | The same pattern in Node, buildable without extra direction | "good we shoudl eb able to do this same thing all in javacript with Node backend" · "as a team on future project without much extra direction" | ADR-0014's Node table; TEAM-11's done item 5 |
| 11:45 | Move the demo passwords into the secrets store, and go on POC-05 | "yes and go on poc-5" | `docs/status.md`; `~/jhc/secrets/kessler-poc/local-demo-logins.env` |
| 12:22 | POC-06 accepted in the browser | "POC-6 looks good in browser - continue to POC-7" | the backlog |
| 13:35 | The seed's long-distance recommendations are acceptable | "yeah its good with a couple of outliers liek that 💪" | the backlog, POC-08's evidence |
| 15:30 | Journal the window for future client-facing documents | "Ok Anne write up this window of work in detail, refer to stories and create .md files that journal all up to deploy and allow future session to mine for client facing docs" | this folder |

## Decided by the team, open to John

| Decision | Who | Why | How to change it |
|---|---|---|---|
| Intake drafting uses `claude-opus-5-5` at low effort | Cesar, with the `claude-api` skill | The skill's rule: Opus 5.5 unless the product owner names another. The plan's first thought was a Sonnet-class model | One line (`MODEL` in `app/backend/ofs/intake.py`); cents of difference at demo volume |
| Writes are serialized in one process | Cesar, from the cold review | It makes id order, commit order and publish order one order, for a single uvicorn process | A second process would need a database lock and an outbox |
| Login limit: 10 a minute per account and address, 60 per address | Orly | It stops guessing, and doesn't lock out an office behind one address | `LOGIN_LIMIT` in `ofs/auth.py` |
| New request: one per person every 3 s | Orly, from the cold review | A public demo login can't flood the board | `SIMULATE_EVERY` in `ofs/api.py` |
