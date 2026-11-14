# Jahnel Group POC: status

Updated: 2026-11-14 (Anne, sprint start passed; POC-02 done)
Kind: prospect
Repo: `~/jhc/prospects/jahnel-poc` · Remote: none yet (John creates it on jhcreative)
App instance: `~/jhc/sites/jahnel-poc` (Tailor v1.1.5), local at http://localhost:9219 · Remote: none yet

## Live

Nothing live.

## Rollback

None.

## Next

**Due Monday 2026-11-16.** The plan was approved 2026-11-14 (`docs/plans/2026-11-13-poc-plan.md`). The sprint start
passed RTS-1..6 (`docs/backlog/2026-11-14-sprint-start.md`). **POC-02 is done:** the instance runs locally, and the
`fieldops` module is mounted through Tailor's own installer, with no POC code in Tailor core (Q7 answered, R3 retired).
Next: POC-03, the tables and the seed (Pete, Jen), with Pete's command and event schemas first (RTS-2).
- **Deploy:** to `ofs.apps.johnhiemstra.com` on a new JHC apps box (OVH VPS-2, edge mode), on John's go Monday.
- **Dry-run report:** Sunday 8 pm.
- **Delivery:** the app, the private repo with invites, the email with the deck attached. Stretch: the narratives in
  an in-app help panel.

## Waiting on John

| Since | Item | Owner | Answer |
|---|---|---|---|
| 2026-11-14 | Order the OVH VPS-2 (US) for the JHC apps box and renew the OVH API token (the trial token expired 2026-10-28) | Rob | |
| 2026-11-14 | Create the repo: `! gh repo create jhcreative/jahnel-poc --private --source ~/jhc/prospects/jahnel-poc --remote origin --push`; the app instance repo follows the same pattern | Cesar | |
| 2026-11-14 | Anthropic API key for intake drafting. `~/jhc/secrets/anthropic.env` already holds an `ANTHROPIC_API_KEY`: use that one, or a separate POC key? Either way, a spend cap and an alert on the account | Cesar | |
| 2026-11-14 | Neale's and Ann-Marie's GitHub usernames, for the repo invites | Anne | |
| 2026-11-14 | Cloudflare: `ofs.apps.johnhiemstra.com` (and `apps.`) A records to the new box, grey cloud | Rob | |
