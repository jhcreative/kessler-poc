#!/usr/bin/env python3
"""Assemble the final presentation: every page-N.html in this folder, landscape 11 x 8.5, in page order, into
../jahnel-poc-final.pdf, with a PNG preview of each page in preview/. Plan: docs/plans/2026-11-16-final-presentation.md.

The pages are the source (PP-11). The text pages (1, 3, 5, 7, 9) are written by hand and this script never writes
them: it formats them with the pinned Prettier, which changes layout only, then renders. The graphic pages
(2, 4, 6, 8) come from their own builder and land here as page-N.html too.

    python3 assemble.py
    python3 assemble.py --with-logins   # also a TEST copy with the demo passwords as an unbranded page 10

The TEST copy is for John's own click-through (2026-11-17) and comes out of the final version. The passwords are read
from the secrets store at render time, set into the page in memory and never written to disk except inside that PDF,
which .gitignore keeps out of the repo.
"""
import io
import re
import sys
from pathlib import Path

KIT = Path.home() / "jhc/jhc-agency/skills/product-ops/writer-brand-kit"
sys.path.insert(0, str(KIT))
from prettier_html import format_html  # noqa: E402  (every PDF's HTML is formatted first, John 2026-10-29)
from playwright.sync_api import sync_playwright  # noqa: E402
from pypdf import PdfReader, PdfWriter  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "jahnel-poc-final.pdf"
TEST = HERE.parent / "jahnel-poc-final-TEST-logins.pdf"
LOGINS = Path.home() / "jhc/secrets/jahnel-poc/box-apps-demo-logins.env"   # the live box's logins
ROLES = {"coord@ofs.com": "Coordinator", "dispatch@ofs.com": "Dispatch", "tech@ofs.com": "Tech",
         "controller@ofs.com": "Controller", "exec@ofs.com": "Overview"}


def logins_page():
    """Page 10, unbranded, for testing only. Built in memory; nothing printed."""
    import html
    pairs = dict(l.split("=", 1) for l in LOGINS.read_text().splitlines() if "=" in l)
    rows = "".join(f"<tr><td>{ROLES.get(e, e)}</td><td>{html.escape(e)}</td><td><code>{html.escape(pw)}</code></td></tr>"
                   for e, pw in pairs.items())
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
      body{{font:14pt -apple-system,Helvetica,Arial,sans-serif;margin:0.8in;color:#111}}
      h1{{font-size:18pt}} td{{padding:8px 18px 8px 0}} code{{font-size:14pt}} p{{color:#a00}}</style></head><body>
      <h1>Test logins: https://ofs.apps.johnhiemstra.com</h1>
      <p>For testing only. Remove before the final version.</p><table>{rows}</table></body></html>"""


def pages():
    found = [(int(m.group(1)), p) for p in HERE.glob("page-*.html") if (m := re.match(r"page-(\d+)", p.name))]
    return [p for _, p in sorted(found)]


def main():
    files = pages()
    if not files:
        sys.exit("no page-N.html here")
    format_html(files)
    (HERE / "preview").mkdir(exist_ok=True)
    w = PdfWriter()
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1056, "height": 816}, device_scale_factor=2)
        for f in files:
            pg.goto(f.as_uri())
            pg.wait_for_load_state("networkidle")
            over = pg.evaluate("""() => { const s = document.querySelector('.sheet'); const b = s.getBoundingClientRect().bottom;
                return Math.max(0, ...[...s.querySelectorAll('*')].map(e => e.getBoundingClientRect().bottom - b)); }""")
            if over > 1:
                print(f"  ! {f.name}: content runs {over:.0f}px past the bottom of the sheet")
            pg.screenshot(path=str(HERE / "preview" / f.with_suffix(".png").name))
            reader = PdfReader(io.BytesIO(pg.pdf(width="11in", height="8.5in", print_background=True)))
            n = len(reader.pages)
            print(f"  {f.name}" + ("" if n == 1 else f"   <-- {n} sheets: the content overflows one page"))
            for p in reader.pages:
                w.add_page(p)
        if "--with-logins" in sys.argv:
            pg.set_content(logins_page())
            test = PdfWriter()
            for p in w.pages:
                test.add_page(p)
            for p in PdfReader(io.BytesIO(pg.pdf(width="11in", height="8.5in"))).pages:
                test.add_page(p)
            with open(TEST, "wb") as fh:
                test.write(fh)
            print("wrote", TEST, len(test.pages), "pages (TEST copy, passwords on page 10, not committed)")
        b.close()
    with open(OUT, "wb") as fh:
        w.write(fh)
    print("wrote", OUT, len(w.pages), "pages; previews in", HERE / "preview")


if __name__ == "__main__":
    main()
