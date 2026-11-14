# POC-11: hardening and the box path (14:34 to 15:29)

**Goal:** DOD-1 (the gate, with evidence), DOD-3 (a cold review), and the deploy dry run to the apps box (R1 verified).
The deploy itself waits on the box.

## The cold review (DOD-3)

A fresh agent read `app/` with the code and its purpose, not our conclusions, and reviewed in DOD-3's order: tests,
then code, then security. It reported 20 findings. **17 are fixed (13 with a test that pins the fix), and 3 are
accepted with a reason.** The full table is `docs/backlog/2026-11-14-cold-review.md`.

The ones worth telling:
- **The high one, real:** event ids are assigned before commit, so two simultaneous commands could publish out of
  order, and a view would silently drop one.
  - **The fix:** writes go one at a time under an in-process lock: write, commit, publish, then let go. That's right
    for a single-process app, and the record says what a second process would need.
  - **Also fixed:** the same lock closed a QuickBooks document-number race.
- **A rail could be walked around:** the priced fields could change after dispatch. Now they're the coordinator's
  alone, fixed once dispatched, and raising an estimate voids the client's approval.
- **Untested behaviour, now tested:**
  - A real two-session race on the row lock. I removed the lock to confirm the test fails, then restored it.
  - A failed commit publishes nothing.
- **Our own slip, caught before commit:** the first cut of the lock held it across the 2 to 4 second Claude call.
- **Our own count, corrected:** I first wrote that 14 fixes had tests. A recount found 13, and the record and the
  unpushed commit message were corrected.

## Orly's checks

- **Secrets:** no key or secret in any image layer or file (three images scanned); `.env` outside both build contexts,
  and excluded anyway.
- **Headers:** the strict CSP, noindex (header, `robots.txt`, meta tag), nosniff, same-origin referrer, a permissions
  policy, and no `Server` header.
- **No mail code anywhere,** so nothing can reach ofs.com.
- **Audits:** `npm audit` and `pip-audit` found 0 known vulnerabilities.

## The box path (Rob, Cesar)

- **`docker-compose.edge.yml`,** Tailor's edge pattern: no host ports, the domain's alias on `tailor-edge`, NET_RAW
  dropped.
- **The site's Caddy trusts only the edge's fixed address** (10.240.0.2) and sends one `X-Forwarded-For`. Without
  that, every visitor would look like the edge and share one login limit.
- **`scripts/ship.sh`:**
  - it requires a clean commit and a green gate, builds linux/amd64 images tagged by commit, refuses a secret in any
    layer, and checks the edge compose;
  - on John's go with a snapshot (OPS-5), it runs `docker save | ssh docker load`, starts the tag, routes the domain,
    seeds and sets the logins on first deploy, then runs `edge.sh check`;
  - it refuses a box `.env` without the edge address and a Secure cookie;
  - `--rollback <tag>` pairs with it.
  - **The dry run is green.**
- **`scripts/check-live.py`, R1's proof:** health, noindex, the CSP, the cookie, and a WebSocket through the real URL
  that hears a new request. **7 of 7 locally,** the event in 1.7 seconds, drafting included.

## State at the end of the window

- **The evidence:** gate 114, vitest 7, e2e 12 (run twice after the fixes), the live check 7 of 7, the ship dry run
  green. `app/` at `aa8594a`.
- **Not done:** the deploy and R1 on the real box. Waiting on John: the VPS-2 order, the OVH token, the GitHub repo
  create, and the Cloudflare DNS records.

## Mineable

- **The cold review is a strong process story:** we asked a fresh reader to find what we missed. It found a real
  ordering bug, and we fixed it the same hour, with a test that fails if anyone undoes it.
