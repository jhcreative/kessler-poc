# Jahnel Group POC: status

Updated: 2026-11-16 (Rob, the box is ready; the first deploy waits on John's go)
Kind: prospect
Repo: `~/jhc/prospects/jahnel-poc` · Remote: `jhcreative/jahnel-poc` (private, main; created 2026-11-16)
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
behind it, labelled; the client-approval rule (C3) is in it too. **POC-08 is done:** dispatch (`dispatch@ofs.com`), with
the recommended tech and the reasons, one-click assign, and a recorded reason for an unqualified pick. **POC-09 is
done:** the tech's phone (`tech@ofs.com`), from assignment through sign-off and close, with needs review from the
field. **POC-10 is done** (`controller@ofs.com`): the billing queue, QuickBooks (simulated) and the aging (POC-14).
**Every view is built, and N1 to N3 run end to end.** **POC-11's local half is done:** the gate and e2e green, the
cold review (20 findings: 17 fixed, 3 accepted; `docs/backlog/2026-11-14-cold-review.md`), Orly's checks clean, and
the ship script and live check ready, with the dry run green. **The deploy waits on the box** (the table below).
Next, while it waits: POC-15, the simulator.
- **The build journal:** `docs/journal/2026-11-14-build/` covers this window story by story. Start at its
  `mining-guide.md` when writing the README, the recap email or the narratives.
- **Demo logins (John, 2026-11-14):** the passwords are in `~/jhc/secrets/jahnel-poc/local-demo-logins.env`.
- **Intake key (John, 2026-11-14):** the demo uses the existing key in `~/jhc/secrets/anthropic.env`. It's read at
  runtime and never copied into the repo or an image.
- **The box (ordered 2026-11-16):** `vps-3e8f42b5.vps.ovh.us` (label `jhc-vps-3e8f42b5`; the API takes the ID), 15.204.245.239 and 2604:2dc0:121::1327, VPS-1, Vint Hill US-EAST-VA-2, $5.75/mo with the snapshot option, Ubuntu 24.04 (checked by `ovh-vps.py info`), John's OVH account.
- **Box prep (2026-11-16, Rob):** rebuilt with John's key (the order didn't install it), `harden-ovh-box.sh` HARDENED, the OVH edge firewall (22/80/443), rDNS to ofs.apps, and the gates: deploy@ ssh and sudo, apt, outbound https, 5432 refused. DNS: `apps` and `ofs.apps` A records, grey cloud. Token: `~/jhc/secrets/ovhcloud/jhc-apps-api.env`, 30 days (to 2026-12-16). Then (John's "go on secrets"): new box demo logins in `~/jhc/secrets/jahnel-poc/box-apps-demo-logins.env`; `/srv/ofs/.env` (secrets generated on the box), `anthropic.env` and `demo-logins.env`, all 0600; the edge from Tailor v1.1.5 `templates/edge/`, healthy on `tailor-edge` 10.240.0.0/24 (80/443 open once a site is routed); snapshot `3ec70dc9` (2026-11-16 21:47 UTC). **Ready for `SNAPSHOT_TAKEN=yes app/scripts/ship.sh --box deploy@15.204.245.239 --first` on John's go.**
- **Deploy:** to `ofs.apps.johnhiemstra.com` on a new JHC apps box (OVH VPS-1, edge mode; VPS-2 out of stock 11-16, US boxes resize up in place), on John's go Monday.
- **Dry-run report:** Sunday 8 pm.
- **Delivery:** the app, the private repo with invites, the email with the deck attached. Stretch: the narratives in
  an in-app help panel.

## Waiting on John

| Since | Item | Owner | Answer |
|---|---|---|---|
| 2026-11-14 | Neale's and Ann-Marie's GitHub usernames, for the repo invites | Anne | |
