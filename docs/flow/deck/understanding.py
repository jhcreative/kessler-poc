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
            f'<text class="h" x="{x+18}" y="{y+h/2-3}"{col}>{name}</text>'
            f'<text class="s" x="{x+18}" y="{y+h/2+14}"{col}>{sub}</text>')


def svg():
    p = [ARROW]
    p.append('<text class="k" x="0" y="96">WAYS IN</text>')
    for i, (n, s) in enumerate([("Target portal", "their format, their rules"), ("Emails", "Starbucks stores, other clients"),
                                ("FacilIT", "smaller clients")]):
        y = 110 + i * 82
        p.append(box(0, y, 190, 60, n, s))
        p.append(line(f"M190,{y+30} C240,{y+30} 240,{190+i*30} 278,{190+i*30}"))
    # job records
    p.append('<path d="M280,148 a95,10 0 0 1 190,0 V292 a95,10 0 0 1 -190,0 Z" fill="#fdf1e1" stroke="#F7941E" stroke-width="1.8"/>'
             '<path d="M280,148 a95,10 0 0 0 190,0" fill="none" stroke="#F7941E" stroke-width="1.8"/>')
    for i, (c, t) in enumerate([("h", "Job records"), ("s", "one record per request"), ("s", "the contract applied"),
                                ("s", "the state, at every step")]):
        p.append(f'<text class="{c}" x="375" y="{196+i*20}" text-anchor="middle">{t}</text>')
    # contracts, below, read-only into job records
    p.append(store(295, 378, 160, 54, "Contracts", "maintained elsewhere, for now", False))
    p.append(line("M375,378 V306"))
    p.append('<text class="e" x="384" y="340">read-only: applied to</text><text class="e" x="384" y="354">this one request</text>')
    # dispatch, onsite (upper lane)
    p.append(line("M470,190 H520 V130 H578"))
    p.append(box(580, 100, 160, 60, "Dispatch", "people, parts, the route"))
    p.append(line("M740,130 H788"))
    p.append(box(790, 100, 160, 60, "Onsite", "the tech at the site"))
    p.append(line("M870,100 V40 H420 V136"))
    p.append('<text class="e" x="645" y="32" text-anchor="middle">back into the record: what the site found, approval needed, signed</text>')
    # billing (lower lane), only after onsite returns
    p.append(line("M470,262 H578"))
    p.append('<text class="e" x="482" y="254">only after onsite</text>')
    p.append(box(580, 232, 160, 60, "Billing", "close to cash"))
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
The record sends the job to dispatch and onsite, takes back what the site found, and only then moves it to billing.</p>
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
out = HERE.parent / "jahnel-poc-flows.pdf"
portrait = PdfReader(str(HERE.parent / "_portrait.pdf"))
w = PdfWriter()
for pdf in (PdfReader(io.BytesIO(land)), portrait):
    for page in pdf.pages:
        w.add_page(page)
with open(out, "wb") as f:
    w.write(f)
print("wrote", out, len(w.pages), "pages")
