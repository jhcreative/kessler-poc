# Jahnel Group POC: status

Updated: 2026-11-17 (Angela, v0.1.1 live; the deck at nine gears)
Kind: prospect
Repo: `~/jhc/prospects/jahnel-poc` · Remote: `jhcreative/jahnel-poc` (private, main; created 2026-11-16)
App: `app/` in this repo, local at http://localhost:9219 (API only until POC-06)

## Live

**https://ofs.apps.johnhiemstra.com**, images `a657757` (v0.1.1, `docs/releases/v0.1.1.md`), shipped 2026-11-17 by John (`ship.sh`) on `vps-3e8f42b5` (15.204.245.239). `check-live.py`: 7 of 7. Demo data reseeded after the check (45 jobs, invoices at the new rate; logins kept). Box logins: `~/jhc/secrets/jahnel-poc/box-apps-demo-logins.env`; they're on page 9 of the PDF too (John, 2026-11-17: the app comes down within the week).

## Delivery (plan `docs/plans/2026-11-16-final-presentation.md`)

- **The PDF, nine pages, drafted:** `docs/flow/jahnel-poc-final.pdf`, from `docs/flow/final/` (text pages 1, 3, 5, 7, 9 are
  hand-edited HTML; graphics 2, 4, 6, 8 from `graphics.py`; `assemble.py` renders). Waits on John's read-through.
- **The video, reshot (take 2):** `docs/delivery/video/jahnel-poc-one-request-five-views.mp4`, 3:16, captioned, Lisa's
  RTP-3 pass met. Waits on John's unlisted upload; then its link goes on page 9 and in the email.
- **The emails:** `docs/delivery/2026-11-16-email.md` and `…-logins-email.md`, Lisa's RTP-3 in. No password in the repo.
- **App fixes, live in v0.1.1:** `919a661` (invoice labor = hours × $150, synthetic), `d53e197` (phone hint after
  approval), `dccedd3` (e2e flake).
- **The PDF carries the passwords on page 9**, filled at render; it's untracked in git.

## Rollback

`ship.sh --box deploy@15.204.245.239 --rollback 110bf61`, or the OVH snapshot `92d5186e` (2026-11-17 15:29 UTC, v0.1.0 running): `ovh-vps.py --env ~/jhc/secrets/ovhcloud/jhc-apps-api.env revert vps-3e8f42b5.vps.ovh.us`. Either is John's (OPS-5).

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
- **Start here next window:** `docs/carry-forward/2026-11-16-1720-live-on-the-apps-box.md` (the box, the keys by name, the permissions, the lessons). Release notes: `docs/releases/v0.1.0.md`.
- **The build journal:** `docs/journal/2026-11-14-build/` covers this window story by story. Start at its
  `mining-guide.md` when writing the README, the recap email or the narratives.
- **Demo logins (John, 2026-11-14):** the passwords are in `~/jhc/secrets/jahnel-poc/local-demo-logins.env`.
- **Intake key (John, 2026-11-14):** the demo uses the existing key in `~/jhc/secrets/anthropic.env`. It's read at
  runtime and never copied into the repo or an image.
- **The box (ordered 2026-11-16):** `vps-3e8f42b5.vps.ovh.us` (label `jhc-vps-3e8f42b5`; the API takes the ID), 15.204.245.239 and 2604:2dc0:121::1327, VPS-1, Vint Hill US-EAST-VA-2, $5.75/mo with the snapshot option, Ubuntu 24.04 (checked by `ovh-vps.py info`), John's OVH account.
- **Box prep (2026-11-16, Rob):** rebuilt with John's key (the order didn't install it), `harden-ovh-box.sh` HARDENED, the OVH edge firewall (22/80/443), rDNS to ofs.apps, and the gates: deploy@ ssh and sudo, apt, outbound https, 5432 refused. DNS: `apps` and `ofs.apps` A records, grey cloud. Token: `~/jhc/secrets/ovhcloud/jhc-apps-api.env`, 30 days (to 2026-12-16). Then (John's "go on secrets"): new box demo logins in `~/jhc/secrets/jahnel-poc/box-apps-demo-logins.env`; `/srv/ofs/.env` (secrets generated on the box), `anthropic.env` and `demo-logins.env`, all 0600; the edge from Tailor v1.1.5 `templates/edge/`, healthy on `tailor-edge` 10.240.0.0/24 (80/443 open once a site is routed); snapshot `3ec70dc9` (2026-11-16 21:47 UTC). Deployed (see Live).
- **Deploy:** to `ofs.apps.johnhiemstra.com` on a new JHC apps box (OVH VPS-1, edge mode; VPS-2 out of stock 11-16, US boxes resize up in place), on John's go Monday.
- **Dry-run report:** Sunday 8 pm.
- **Delivery:** the app, the private repo with invites, the email with the deck attached. Stretch: the narratives in
  an in-app help panel.

## Waiting on John

| Since | Item | Owner | Answer |
|---|---|---|---|
| 2026-11-14 | Neale's and Ann-Marie's GitHub usernames, for the repo invites | Anne | |
| 2026-11-16 | Tag v0.1.0 at `110bf61` (`git tag v0.1.0 110bf61 && git push origin v0.1.0`), or leave it untagged for a POC | Cesar | |
| 2026-11-16 | Your click-through of the five views on the live site; say if you want the demo data reseeded (request 1046 is the live check's) | Angela | |
| 2026-11-17 | Read the nine-page PDF; edit the text pages by hand if you like | Angela | |
| 2026-11-17 | Upload the demo video to YouTube, **unlisted**, and send the link | Henry | |
| 2026-11-17 | The email's address: "Ann-Marie, Neale" (recommended) or "Dana" in the role play; keep or flatten its two point labels | Lisa | |
