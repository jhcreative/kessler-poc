#!/usr/bin/env python3
"""The post-deploy gate, and risk R1's proof: run against the real URL, it checks what a visitor gets.

    check-live.py <base-url> --logins <file of email=password lines>

1. /api/health answers 200, and reads the database (jobs > 0).
2. The page carries noindex (the header and robots.txt) and the strict CSP.
3. exec@ signs in; the cookie is HttpOnly, and Secure on https.
4. R1: a WebSocket opens through the URL (on the box: the edge Caddy, the site's Caddy, the backend) and says hello.
   Then the coordinator sends in a new request over HTTP, and the exec's socket hears it within 10 s.

Step 4 creates one draft job, labelled the simulator, as the demo's New request does. Prints PASS or FAIL per check;
exit 0 only if all pass. Passwords are read from the file and never printed.
"""

from __future__ import annotations

import argparse
import asyncio
import http.cookiejar
import json
import sys
import time
import urllib.request
from urllib.parse import urlparse

from websockets.asyncio.client import connect

results: list[tuple[bool, str]] = []


def check(ok: bool, what: str) -> None:
    results.append((ok, what))
    print(f"{'PASS' if ok else 'FAIL'}  {what}")


class Session:
    def __init__(self, base: str) -> None:
        self.base = base
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))

    def call(self, method: str, path: str, body: object | None = None) -> tuple[int, dict[str, str], bytes]:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method,
                                     headers={"content-type": "application/json", "origin": self.base})
        try:
            with self.opener.open(req, timeout=30) as r:
                return r.status, dict(r.headers), r.read()
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), e.read()

    def cookie(self) -> str:
        return "; ".join(f"{c.name}={c.value}" for c in self.jar)


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("--logins", required=True)
    args = ap.parse_args()
    base = args.base.rstrip("/")
    secure = urlparse(base).scheme == "https"
    logins = dict(line.strip().split("=", 1) for line in open(args.logins) if "=" in line)

    anon = Session(base)
    status, _, body = anon.call("GET", "/api/health")
    jobs = json.loads(body).get("jobs", 0) if status == 200 else 0
    check(status == 200 and jobs > 0, f"health 200, reading the database ({jobs} jobs)")
    status, headers, _ = anon.call("GET", "/")
    lower = {k.lower(): v for k, v in headers.items()}
    check("noindex" in lower.get("x-robots-tag", ""), "X-Robots-Tag noindex")
    check("frame-ancestors 'none'" in lower.get("content-security-policy", ""), "the strict CSP")
    _, _, robots = anon.call("GET", "/robots.txt")
    check(b"Disallow: /" in robots, "robots.txt disallows everything")

    execu = Session(base)
    status, headers, _ = execu.call("POST", "/api/auth/login", {"email": "exec@ofs.com", "password": logins["exec@ofs.com"]})
    cookie = {k.lower(): v for k, v in headers.items()}.get("set-cookie", "").lower()
    check(status == 200 and "httponly" in cookie and (not secure or "secure" in cookie),
          f"exec signs in; the cookie is HttpOnly{' and Secure' if secure else ''}")

    ws_url = ("wss://" if secure else "ws://") + urlparse(base).netloc + "/api/ws"
    try:
        async with connect(ws_url, additional_headers={"Cookie": execu.cookie(), "Origin": base}, open_timeout=10) as ws:
            hello = json.loads(await asyncio.wait_for(ws.recv(), 10))
            check(hello.get("type") == "hello", f"R1: the WebSocket opens through {urlparse(base).netloc} and says hello")
            coord = Session(base)
            coord.call("POST", "/api/auth/login", {"email": "coord@ofs.com", "password": logins["coord@ofs.com"]})
            started = time.monotonic()
            status, _, body = coord.call("POST", "/api/intake/simulate")
            number = json.loads(body)["job"]["number"] if status == 200 else None
            heard = None
            while time.monotonic() - started < 10:
                msg = json.loads(await asyncio.wait_for(ws.recv(), 10))
                if msg.get("type") == "event" and msg["job"]["number"] == number:
                    heard = time.monotonic() - started
                    break
            check(heard is not None, f"R1: a new request (job {number}) reached the open socket"
                  + (f" in {heard * 1000:.0f} ms, drafting included" if heard else ""))
    except Exception as exc:  # any failure to connect is the finding
        check(False, f"R1: the WebSocket failed: {type(exc).__name__}: {exc}")

    failed = [w for ok, w in results if not ok]
    print(f"\n{len(results) - len(failed)} of {len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
