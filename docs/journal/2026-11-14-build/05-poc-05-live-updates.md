# POC-05: live updates (11:45 to 11:59)

**Goal:** G1. A change in any view appears in every other open view within a second, and a view that reconnects
misses nothing.

## Built

- **`ofs/hub.py`:** one queue per open view, in process (one uvicorn process; plan §4). It publishes only after the
  commit. A tech hears only about jobs that are, or just stopped being, theirs.
- **`ofs/ws.py`** (`/api/ws?after=<last id>`):
  - it subscribes before reading the replay, so nothing falls in the gap, then drops anything already sent;
  - it pings every 25 seconds;
  - a view too far behind is told to reload;
  - it's refused without the login cookie (4401) or from another site's origin (4403).

## Verified

- 67 tests passed. The socket tests run against a real server (uvicorn in the test's own event loop), with real
  WebSocket clients and real cookies.
- **On the running stack,** the coordinator's open socket heard the dispatcher assign job 1013 in **21 ms**.

## Found

- **A defect caught by the gate's own run time:** the suite took 326 seconds. A server-side socket waiting on its
  queue missed the client's close until the next ping, so dead connections lingered. It now watches for the
  disconnect alongside the queue; the suite dropped to 24 seconds, and a test pins it.

## Mineable

- **"21 ms"** is a fair, measured number for G1 on a local stack. On the box, the live check measures it through the
  edge (`check-live.py`); use that number once it exists.
