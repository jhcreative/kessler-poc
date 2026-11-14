# Sprint start, 2026-11-14: RTS-1..6 (Angela, Anne)

The committed stories are POC-02 to POC-11 (ranks 3–12, protected). Each gate was checked against the plan
(`docs/plans/2026-11-13-poc-plan.md`, §13) and against what's on disk today.

| Gate | Result | Evidence |
|---|---|---|
| RTS-1 Requirements are testable | **Pass** | Plan §2: every criterion is demonstrable live. POC-02's acceptance, made exact: `GET /api/modules/fieldops/health` answers 200 from its own table, `fieldops` is in the generated module registry, its Alembic branch is at head, and its tests run in the instance suite |
| RTS-2 The contract is defined | **Pass for POC-02; owed before POC-03 and POC-04** | POC-02's contract is `module.json` and the `Health` schema in `router.py`. Pete writes the Pydantic schemas for the commands and the event envelope (§4, §5) first, before the POC-03 and POC-04 code |
| RTS-3 Dependencies are identified | **Pass** | Tailor v1.1.5 (`3d53021e`), scaffold deps installed, Docker 29.4.1 up, ports 9219/6219 claimed. The box, the OVH token, DNS, the repo and the invites wait on John and block only POC-11 and POC-16. QuickBooks and the fleet are simulated |
| RTS-4 Test strategy exists | **Pass** | `docs/plans/2026-11-14-test-strategy.md` (Jen), with what we deliberately don't test |
| RTS-5 The branch is clean | **Pass** | New instance repo on `main` from the scaffold's own commit (`21def9f`). Starting-state gate: backend pytest green before any POC-03 code. One builder in this window, so no lanes; a second window takes its own worktree (PP-13) |
| RTS-6 Privacy goes to Orly first | **Pass for POC-02; Orly's design notes bind POC-03 to POC-05** | POC-02 holds no personal data. Orly's notes, below |

## Orly's design notes (RTS-6), for POC-03 to POC-05

- **Synthetic only.** Role names (Coordinator 1, Tech 4), fictional clients, generated sites. FacilIT is a real product
  named as a channel, not a person or a customer record.
- **Demo logins.** Five accounts at `ofs.com`, one per role, passwords in `~/jhc/secrets` under the site's dir. Every
  command checks the caller's ops role on the server; the view hiding a button is not the control.
- **No mail to ofs.com.** It's a real domain. `RESEND_*` stays unset on this instance, so password reset answers 503
  and sends nothing. Checked again at the dry run.
- **WebSocket.** Authenticated by the session cookie at the upgrade, with an `Origin` check. Topics are filtered by
  role on the server: a tech subscribes to their own queue only.
- **Claude.** Only synthetic intake text is sent. The key stays in `~/jhc/secrets`, never in the repo or an image
  layer. Tokens are logged per job event, not the prompt's content.
- **Public surface.** `noindex` on every `/ops` route and in `robots.txt` before the deploy. `/health` names a count
  only.
