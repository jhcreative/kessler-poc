#!/usr/bin/env python3
"""Assemble the final presentation: every page-N.html in this folder, landscape 11 x 8.5, in page order, into
../kessler-poc-final.pdf, with a PNG preview of each page in preview/. Plan: docs/plans/2026-11-16-final-presentation.md.

The pages are the source (PP-11). The text pages (1, 3, 5, 7, 9) are written by hand and this script never writes
them: it formats them with the pinned Prettier, which changes layout only, then renders. The graphic pages
(2, 4, 6, 8) come from their own builder and land here as page-N.html too.

    python3 assemble.py

Page 9 lists the demo passwords (John, 2026-11-17: "risk is minimal, will pull the live app down within the week").
The page's source holds placeholders, {{password:<email>}}; they're filled in the browser, in memory, from the secrets
store, after the preview is taken. So the passwords live only inside the PDF, and .gitignore keeps the PDF out of git.
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
OUT = HERE.parent / "kessler-poc-final.pdf"
LOGINS = Path.home() / "jhc/secrets/kessler-poc/box-apps-demo-logins.env"   # the live box's logins
FILL = r"""(pw) => { const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let n, left = 0;
  while ((n = w.nextNode())) n.nodeValue = n.nodeValue.replace(/\{\{password:([^}]+)\}\}/g, (m, e) => pw[e] ?? m);
  w.currentNode = document.body; while ((n = w.nextNode())) if (n.nodeValue.includes("{{password:")) left++;
  return left; }"""


def passwords():
    """The live box's demo logins, read at render time; nothing printed."""
    return dict(l.split("=", 1) for l in LOGINS.read_text().splitlines() if "=" in l)



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
            pg.screenshot(path=str(HERE / "preview" / f.with_suffix(".png").name))  # before the fill: no passwords
            if "{{password:" in f.read_text():
                if pg.evaluate(FILL, passwords()):
                    sys.exit(f"STOP: {f.name} has a password placeholder the secrets store can't fill")
            over = pg.evaluate("""() => { const s = document.querySelector('.sheet'); const b = s.getBoundingClientRect().bottom;
                return Math.max(0, ...[...s.querySelectorAll('*')].map(e => e.getBoundingClientRect().bottom - b)); }""")
            if over > 1:
                print(f"  ! {f.name}: content runs {over:.0f}px past the bottom of the sheet")
            reader = PdfReader(io.BytesIO(pg.pdf(width="11in", height="8.5in", print_background=True)))
            n = len(reader.pages)
            print(f"  {f.name}" + ("" if n == 1 else f"   <-- {n} sheets: the content overflows one page"))
            for p in reader.pages:
                w.add_page(p)
        b.close()
    with open(OUT, "wb") as fh:
        w.write(fh)
    print("wrote", OUT, len(w.pages), "pages; previews in", HERE / "preview")


if __name__ == "__main__":
    main()
