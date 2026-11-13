#!/usr/bin/env python3
"""Landscape page 1 (11 x 8.5): our high-level understanding, one request's flow, left to right (John, 2026-11-13).
Writes _landscape-1.html (underscore: the portrait assembler skips it), renders it, and puts it in front of the
portrait deck as ../jahnel-poc-flows.pdf. A flow diagram, not system architecture: no vendors or tools on it."""
import io, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import build
from build import MASTHEAD, META, STYLE, ARROW, line, store
from playwright.sync_api import sync_playwright
from pypdf import PdfReader, PdfWriter

HERE = Path(__file__).resolve().parent


def box(x, y, w, h, name, sub, dark=False):
    fill, stroke, col = ("#1c1b19", "#1c1b19", ' style="fill:#fff"') if dark else ("#fff", "#9a968f", "")
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1.3"/>'
            f'<rect x="{x}" y="{y}" width="5" height="{h}" rx="2" fill="#F7941E"/>'
            f'<text class="h" x="{x+16}" y="{y+h/2-3}" style="font-weight:700;font-size:14.5px{";fill:#fff" if dark else ""}">{name}</text>'
            f'<text class="s" x="{x+16}" y="{y+h/2+14}" style="font-size:11px{";fill:#fff" if dark else ""}">{sub}</text>')


def svg():
    p = [ARROW]
    p.append('<text class="k" x="0" y="96">WAYS IN</text>')
    for i, (n, s) in enumerate([("Target portal", "Their format, their rules."), ("Emails", "Starbucks stores, other clients."),
                                ("FacilIT", "Smaller clients.")]):
        y = 110 + i * 82
        p.append(box(0, y, 170, 60, n, s))
        p.append(line(f"M170,{y+30} C212,{y+30} 212,{190+i*30} 248,{190+i*30}"))
    mid = len(p)  # everything after the ways in shifts left 20 to make room on the right
    # job records
    p.append('<path d="M270,148 a105,10 0 0 1 210,0 V292 a105,10 0 0 1 -210,0 Z" fill="#fdf1e1" stroke="#F7941E" stroke-width="1.8"/>'
             '<path d="M270,148 a105,10 0 0 0 210,0" fill="none" stroke="#F7941E" stroke-width="1.8"/>')
    p.append('<text class="h" x="360" y="190" text-anchor="middle" style="font-weight:700;font-size:15px">Job records</text>')
    for i, t in enumerate(["One record per request.", "Contract guardrails", "applied to request.",
                           "Maintains record state", "from Intake to Collections."]):
        p.append(f'<text class="s" x="360" y="{210+i*14.5}" text-anchor="middle" style="font-size:11px">{t}</text>')
    # inside the record: onsite feedback enters, billing exits
    p.append(line("M458,154 V262 H478", dash=True))
    # contracts, below, read-only into job records
    p.append(store(295, 378, 160, 54, "Contracts", "Maintained elsewhere, for now.", False))
    p.append(line("M375,378 V306"))
    p.append('<text class="e" x="384" y="340">Read-only: applied to</text><text class="e" x="384" y="354">this one request.</text>')
    # dispatch, onsite (upper lane)
    p.append(line("M480,190 H525 V130 H578"))
    p.append(box(580, 100, 160, 60, "Dispatch", "People, parts, the route."))
    p.append(line("M740,130 H788"))
    p.append(box(790, 100, 160, 60, "Onsite", "The tech at the site."))
    p.append(line("M870,100 V40 H458 V136"))
    p.append('<path d="M660,100 V70 V40" fill="none" stroke="#1c1b19" stroke-width="1.3" marker-mid="url(#ar)"/>')  # dispatch reports back into the record too (John, 2026-11-13)
    p.append('<text class="e" x="645" y="32" text-anchor="middle">Back into the record: what the site found, approval needed, signed.</text>')
    # billing (lower lane), only after onsite returns
    p.append(line("M480,262 H538"))
    p.append('<text class="e" x="485" y="243">Only after</text><text class="e" x="485" y="255">onsite.</text>')
    p.append(box(540, 232, 120, 60, "Billing", "Matched to the job."))
    p.append(line("M660,262 H683"))
    p.append(box(685, 232, 155, 60, "Invoicing", "Multiple client formats."))
    p.append(line("M840,262 H863"))
    p.append(box(865, 232, 105, 60, "Collections", "Aging, disputes."))
    p[mid:] = ['<g transform="translate(-20,0)">'] + p[mid:] + ['</g>']
    return f'<svg class="fig" viewBox="-2 -2 954 440" xmlns="http://www.w3.org/2000/svg" style="width:9.5in;margin-top:22px">{"".join(p)}</svg>'


LAND = """<style>
  .sheet{width:11in;height:8.5in;padding:0.55in 0.75in 0.45in;}
  @media print{@page{size:11in 8.5in;margin:0;}}
  .title{margin-top:20px;}
</style>"""

html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>OneFamilyServices: how one request flows</title>
<link rel="stylesheet" href="common.css"><link rel="stylesheet" href="components.css">{STYLE}{LAND}</head>
<body><div class="sheet">
{MASTHEAD}
<h1 class="title">How One Request Flows</h1>
<div class="meta">{META}</div>
<p class="dek">Every request lands in one job record, which pulls its contract read-only and applies it to that request.
The record sends the job to dispatch and onsite, takes back what the site found, and only then moves it on to billing, invoicing and collections.</p>
{svg()}
<div class="folio">1</div>
</div></body></html>
"""
src = HERE / "_landscape-1.html"
src.write_text(html)
with sync_playwright() as pw:
    b = pw.chromium.launch(); pg = b.new_page()
    pg.goto(src.as_uri()); pg.wait_for_load_state("networkidle")
    land = pg.pdf(width="11in", height="8.5in", print_background=True, prefer_css_page_size=False)
    b.close()
# Page one alone for now (John, 2026-11-13); --with-rest puts it in front of the portrait deck.
rest = "--with-rest" in sys.argv
out = HERE.parent / ("jahnel-poc-flows.pdf" if rest else "jahnel-poc-understanding.pdf")
w = PdfWriter()
for pdf in [PdfReader(io.BytesIO(land))] + ([PdfReader(str(HERE.parent / "_portrait.pdf"))] if rest else []):
    for page in pdf.pages:
        w.add_page(page)
with open(out, "wb") as f:
    w.write(f)
print("wrote", out, len(w.pages), "pages")
