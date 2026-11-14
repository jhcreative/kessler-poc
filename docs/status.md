# Jahnel Group POC: status

Updated: 2026-11-14 (Anne, plan approved; build started)
Kind: prospect
Repo: `~/jhc/prospects/jahnel-poc` · Remote: none yet (John creates it; org to confirm)

## Live

Nothing live.

## Rollback

None.

## Next

**Due Monday 2026-11-16.** The plan was approved 2026-11-14 (`docs/plans/2026-11-13-poc-plan.md`, walkthrough
answered). The build is under way from POC-02: a Tailor instance, the `fieldops` module, websockets, AG Grid Community,
Claude intake drafting.
- **Deploy:** to `ofs.apps.johnhiemstra.com` on a new JHC apps box (OVH VPS-2, edge mode), on John's go Monday.
- **Dry-run report:** Sunday 8 pm.
- **Delivery:** the app, the private repo with invites, the email with the deck attached. Stretch: the narratives in
  an in-app help panel.

## Waiting on John

| Since | Item | Owner | Answer |
|---|---|---|---|
| 2026-11-14 | Order the OVH VPS-2 (US) for the JHC apps box and renew the OVH API token (the trial token expired 2026-10-28) | Rob | |
| 2026-11-14 | Create the repo: `! gh repo create jhcreative/jahnel-poc --private --source ~/jhc/prospects/jahnel-poc --remote origin --push`; the app instance repo follows the same pattern | Cesar | |
| 2026-11-14 | Anthropic API key for intake drafting into `~/jhc/secrets` (a POC key, spend cap and alert set on the account) | Cesar | |
| 2026-11-14 | Neale's and Ann-Marie's GitHub usernames, for the repo invites | Anne | |
| 2026-11-14 | Cloudflare: `ofs.apps.johnhiemstra.com` (and `apps.`) A records to the new box, grey cloud | Rob | |
