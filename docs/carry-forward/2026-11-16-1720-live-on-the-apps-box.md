# Carry-forward 2026-11-16 17:20: the POC is live on the new apps box, 7 of 7 (Anne)

## State

- **Live:** https://ofs.apps.johnhiemstra.com, tag `110bf61` (`app/` is byte-for-byte the gated `aa8594a`), shipped by
  John's own `! … ship.sh --first`. `check-live.py`: 7 of 7. Release notes: `docs/releases/v0.1.0.md`.
- **The box:** JHC's apps box, on John's OVH US account.

  | Field | Value |
  |---|---|
  | Service (the API takes this) | `vps-3e8f42b5.vps.ovh.us` (the panel label `jhc-vps-3e8f42b5` answers 404) |
  | IPs | 15.204.245.239 · 2604:2dc0:121::1327 |
  | Plan | VPS-1 2027 (2 vCPU, 4 GB, 40 GB), $5.75/mo with the snapshot option. VPS-2 was out of stock; US boxes resize up in place |
  | Datacenter | Vint Hill US-EAST-VA-2 |
  | OS | Ubuntu 24.04.4, rebuilt 11-16 with John's `id_ed25519` (the order hadn't installed it) |
  | Hardening | `harden-ovh-box.sh` HARDENED; OVH edge firewall 22/80/443; rDNS → ofs.apps; 5432 refused from outside |
  | Edge | Tailor v1.1.5 `templates/edge/` at `/srv/_edge`, healthy, network `tailor-edge` 10.240.0.0/24, edge at .2 |
  | App | `/srv/ofs`: compose project `ofs` (postgres, migrate, backend, web), images loaded, no registry |
  | Room | 8% disk, 3.2 GB memory free before the app |
  | Snapshot | `3ec70dc9`, 2026-11-16 21:47 UTC: the prepped box with the edge, **before** the app |

- **DNS (Cloudflare, johnhiemstra.com zone):** A `apps` and A `ofs.apps` → 15.204.245.239, grey cloud. No AAAA yet.
- **Repo:** `jhcreative/kessler-poc`, private, `main` tracks origin; everything here is pushed. No tag yet (tagging
  v0.1.0 is John's, OPS-5).

## Where the keys are (names only)

| What | Where |
|---|---|
| OVH API token for this box, 30 days to **2026-12-16** | `~/jhc/secrets/ovhcloud/jhc-apps-api.env` (600). Rights: `GET /vps`, `/vps/*` all verbs, `/ip/15.204.245.239` and `/*` |
| Box demo logins (5, new, not the local ones) | `~/jhc/secrets/kessler-poc/box-apps-demo-logins.env` (600) |
| Box app secrets (Postgres password, SESSION_SECRET) | generated **on the box** into `/srv/ofs/.env` (600); never on the Mac |
| Anthropic key | `~/jhc/secrets/anthropic.env` → `/srv/ofs/anthropic.env` (600), sent over ssh stdin, never printed |
| Logins on the box | `/srv/ofs/demo-logins.env`, **owned 10001:10001, mode 600** (the container's `app` user) |

Jess's token (`ovhcloud/jess-ship-api.env`, to 12-11) reads this box too (`/vps/*` is account-wide) but has no
`/ip/` rights for it. Use the jhc-apps token here.

## Permissions (what the next window can and can't run)

The allow rules live in **`~/jhc/jhc-agency/.claude/settings.local.json`**, so they apply to a session started in
`~/jhc/jhc-agency`. A session started in `~/jhc/prospects/kessler-poc` doesn't get them: start there from
jhc-agency, or John adds them to that project too (at the prompt, `/permissions`).

| Allowed (John, 11-16) | Not allowed: John runs it with `!` at the prompt, or adds a rule |
|---|---|
| `ssh ubuntu@15.204.245.239 …` | `app/scripts/ship.sh` real runs (redeploy, `--rollback`) |
| `ssh deploy@15.204.245.239 …` | `ovh-vps.py revert` (the snapshot rollback) |
| `harden-ovh-box.sh 15.204.245.239` | `gh repo create`, repo invites |
| `nc -z … 15.204.245.239 5432`, `dig +short -x 15.204.245.239` | anything editing `~/jhc/secrets` (ask first) |

`ovh-vps.py` (info, snapshot, firewall-web, rdns, rebuild) ran without a rule this session. A rebuild still waits on
John's word, because it wipes the box.

## Records

- `docs/releases/v0.1.0.md`: the release, the evidence and the rollback.
- `docs/status.md`: Live, Rollback and the box, updated through the day.
- `docs/journal/2026-11-14-build/12-the-box-and-the-first-deploy.md`: the window for client docs.
- `app/scripts/ship.sh` 65f66ff: the logins-owner gate (PP-12).
- jhc-agency `docs/for-john.md`, regenerated at each status change.
- Memory: `project_jhc_apps_box` (VPS-1, resize later); `feedback_working_with_john` (say where each command is
  typed).

## Tradeoffs

- **VPS-1, not the planned VPS-2.** We give up headroom (40 GB, 4 GB) for a Monday delivery. Fine for the POC
  (8% disk). Resize up when curationapp.com lands; it only works because the box is in the US.
- **Rebuild instead of adding the key in the panel.** It cost about 2 minutes on an empty box, and gave a known
  state with a new host key we could check.
- **The snapshot holds the prepped box, not the running app.** So a revert today goes back to before the deploy.
  Take a new one (one slot) before the next deploy.
- **The edge from Tailor v1.1.5's files, copied by hand.** We skipped `provision-site.sh --edge`, because this isn't
  a Tailor site. The files are identical to develop's.

## Lessons

- **A bind-mounted secret needs the container's owner, not ours.** The first box run stopped at step 6 (route and
  seed done) with `PermissionError: /tmp/logins.env`. The file was `deploy:600`; the backend runs as uid 10001.
  Fixed by `chown 10001:10001` and re-running the step. **It's a gate now:** `ship.sh` step 4 refuses a first deploy
  unless the file is `10001:600` (65f66ff). The header says so too.
- **The OVH US order may not install the SSH key.** `ssh ubuntu@` answered `Permission denied (publickey)`.
  `ovh-vps.py rebuild --key` fixes it; add the check to the deploy-ovhcloud-vps skill's §0 (Rob, next session).
- **Read back a typed IP.** `apps` went in as `12.204…`; a `dig` caught it.
- **An empty edge refuses port 80.** It listens only once a site is routed. That's expected, not a firewall fault.
- **In zsh, `"$t:templates/…"` is the `:t` modifier.** Write `"${t}:path"` for a `git show` with a variable tag.

## Next priority

1. **The delivery, today:** the invites (needs the usernames), then the email with the deck. The README and recap
   draw from `docs/journal/2026-11-14-build/mining-guide.md`. It's next because it's the commitment.
2. **John's own click-through** of the five views on his phone and laptop, against the live site.
3. **Reseed if John wants clean demo data:** the live check left request 1046. A redeploy or reseed is on his go.
4. **POC-15, the simulator** (the stretch): the plan is in the 2026-11-14 carry-forward's "while the box waits".
5. **Rob:** the AAAA records once ufw's v6 rules for 80/443 are checked; the §0 key check in the skill; B2 backups
   are a known gap (the demo data is reseedable, so it's low risk).

## Waiting on John

| Since | Item | Owner | Answer |
|---|---|---|---|
| 2026-11-14 | Neale's and Ann-Marie's GitHub usernames, for the repo invites | Anne | |
| 2026-11-16 | Tag v0.1.0 at `110bf61` (`git tag v0.1.0 110bf61 && git push origin v0.1.0`), or leave it untagged for a POC | Cesar | |
| 2026-11-16 | Your click-through of the five views on the live site; say if you want the demo data reseeded (request 1046 is the live check's) | Angela | |
