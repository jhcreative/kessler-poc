# The box and the first deploy (2026-11-16)

**Goal:** the POC live at ofs.apps.johnhiemstra.com, on a new JHC apps box, by Monday.

## The box

- John ordered it. The planned VPS-2 was out of stock, so it's a VPS-1 in Vint Hill, VA, at $5.75 a month with the
  snapshot option. A US box resizes up in place later; a box outside the US never can.
- The API confirmed Ubuntu 24.04 before anything ran on it. That check exists because an earlier OVH box arrived on
  26.04.
- The key the order should have installed wasn't there. A rebuild with John's key took 54 seconds, and SSH answered
  10 seconds later with a new host key and no `deploy` user: proof it was the fresh system.
- Hardening is one command with a gate after every phase: password and root login off (read from the effective
  config), the firewall, UTC, fail2ban, Docker. Then the OVH edge firewall and reverse DNS.

## The secrets

The app's database password and session secret were generated on the box and never existed on the laptop. The five
demo passwords are new for the box. The Claude key went over ssh without being printed.

## The deploy

John ran it himself. It stopped once, at the last step: the logins file was readable only by the deploy user, and
the app's container runs as its own user. The route and the data had landed. The fix was one ownership change and
the step again. The script now refuses to start unless that file has the right owner, so the slip can't repeat.

Then the live check, 7 of 7: health, HTTPS-only cookies, the security headers, search engines shut out, and the
real-time socket through the edge, with a new request drafted by Claude and on screen in about 4 seconds.

## Numbers

| What | Value |
|---|---|
| Rebuild | 54 s, SSH at +10 s |
| Snapshot | 305 s |
| Disk used before the app | 8% of 38 GB |
| Live checks | 7 of 7 |
| New request to screen, through the edge | 4277 ms, drafting included |
