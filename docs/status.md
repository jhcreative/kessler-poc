# Jahnel Group POC: status

Updated: 2026-11-14 (Anne, POC-07 done)
Kind: prospect
Repo: `~/jhc/prospects/jahnel-poc` · Remote: none yet (John creates it on jhcreative)
App: `app/` in this repo, local at http://localhost:9219 (API only until POC-06)

## Live

Nothing live.

## Rollback

None.

## Next

**Due Monday 2026-11-16.** The plan was approved 2026-11-14, and the sprint start passed RTS-1..6. **John's call: the
app is built from Tailor's parts, not as a Tailor site** (ADR `2026-11-14-tailor-parts-not-a-tailor-site.md`; saved for
future apps as agency ADR-0014). **POC-02 (lean), POC-03 and POC-04 are done:** typed tables, a deterministic seed,
the commands with their rails, the five role logins, and live updates over a WebSocket with replay. **POC-06 is done:**
the live overview at http://localhost:9219 (sign in as `exec@ofs.com`), typed end to end, with a browser e2e. **POC-07
is done:** the coordinator workspace (`coord@ofs.com`), with Claude drafting each new request and the rules standing
behind it, labelled; the client-approval rule (C3) is in it too. Next: POC-08, dispatch with the recommended tech.
- **Demo logins (John, 2026-11-14):** the passwords are in `~/jhc/secrets/jahnel-poc/local-demo-logins.env`.
- **Intake key (John, 2026-11-14):** the demo uses the existing key in `~/jhc/secrets/anthropic.env`. It's read at
  runtime and never copied into the repo or an image.
- **Deploy:** to `ofs.apps.johnhiemstra.com` on a new JHC apps box (OVH VPS-2, edge mode), on John's go Monday.
- **Dry-run report:** Sunday 8 pm.
- **Delivery:** the app, the private repo with invites, the email with the deck attached. Stretch: the narratives in
  an in-app help panel.

## Waiting on John

| Since | Item | Owner | Answer |
|---|---|---|---|
| 2026-11-14 | Order the OVH VPS-2 (US) for the JHC apps box and renew the OVH API token (the trial token expired 2026-10-28) | Rob | |
| 2026-11-14 | Create the repo: `! gh repo create jhcreative/jahnel-poc --private --source ~/jhc/prospects/jahnel-poc --remote origin --push`; the app instance repo follows the same pattern | Cesar | |
| 2026-11-14 | Neale's and Ann-Marie's GitHub usernames, for the repo invites | Anne | |
| 2026-11-14 | Cloudflare: `ofs.apps.johnhiemstra.com` (and `apps.`) A records to the new box, grey cloud | Rob | |
