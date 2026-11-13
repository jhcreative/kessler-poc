#!/usr/bin/env python3
"""Landscape pages (11 x 8.5), left to right (John, 2026-11-13): 1 the recommended request flow, 2 the current one.
Writes _landscape-N.html (underscore: the portrait assembler skips it), renders it, and puts it in front of the
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
    """A step: bold name, then one or more short sentence-case lines."""
    subs = [sub] if isinstance(sub, str) else sub
    fill, stroke = ("#1c1b19", "#1c1b19") if dark else ("#fff", "#9a968f")
    top = y + h / 2 - 3 - 7 * (len(subs) - 1)
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1.3"/>',
           f'<rect x="{x}" y="{y}" width="5" height="{h}" rx="2" fill="#F7941E"/>',
           f'<text class="h" x="{x+16}" y="{top}" style="font-weight:700;font-size:14.5px{";fill:#fff" if dark else ""}">{name}</text>']
    for i, t in enumerate(subs):
        out.append(f'<text class="s" x="{x+16}" y="{top+17+i*14}" style="font-size:11px{";fill:#fff" if dark else ""}">{t}</text>')
    return "".join(out)


def stack(x, y, w, h, rx, fill, stroke):
    """Two offset sheets behind a box: many client formats (John, 2026-11-13). Drawn before the box."""
    return "".join(f'<rect x="{x+d}" y="{y-d}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" '
                   f'stroke-width="1.1"/>' for d in (8, 4))


def human(x, y, label):
    """Human in the loop: a small chip, the by-hand scheme darkened, black border (John, 2026-11-13). It sits on a
    system step where a person reviews or decides."""
    w = len(label) * 5.7 + 22
    return (f'<rect x="{x}" y="{y}" width="{w}" height="20" rx="4" fill="#eadbc4" stroke="#1c1b19" stroke-width="1.1"/>'
            f'<circle cx="{x+10}" cy="{y+7}" r="2.8" fill="#1c1b19"/>'
            f'<path d="M{x+5},{y+16.5} a5,5.5 0 0 1 10,0 Z" fill="#1c1b19"/>'
            f'<text x="{x+19}" y="{y+14}" style="font-size:10px;font-weight:600;fill:#1c1b19">{label}</text>')


def manual(x, y, w, h, name, subs):
    """A manual junction: a person moves the request by hand. Rounded, the human-in-the-loop fill and black border, BY HAND kicker,
    so it never reads as a system step (John, 2026-11-13)."""
    subs = [subs] if isinstance(subs, str) else subs
    top = y + h / 2 + 4 - 7 * (len(subs) - 1)
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="#eadbc4" stroke="#1c1b19" stroke-width="1.6"/>',
           f'<text class="k" x="{x+14}" y="{y+16}" style="fill:#9a5a00;font-size:9px">BY HAND</text>',
           f'<text class="h" x="{x+14}" y="{top}" style="font-weight:700;font-size:14.5px">{name}</text>']
    for i, t in enumerate(subs):
        out.append(f'<text class="s" x="{x+14}" y="{top+17+i*14}" style="font-size:11px">{t}</text>')
    return "".join(out)


def cylinder(x, y, w, h, title, lines, cx, dy=0, ty=None):
    p = [f'<path d="M{x},{y} a{w/2},10 0 0 1 {w},0 V{y+h} a{w/2},10 0 0 1 {-w},0 Z" fill="#fdf1e1" stroke="#F7941E" stroke-width="1.8"/>',
         f'<path d="M{x},{y} a{w/2},10 0 0 0 {w},0" fill="none" stroke="#F7941E" stroke-width="1.8"/>',
         f'<text class="h" x="{cx}" y="{ty if ty else y+42+dy}" text-anchor="middle" style="font-weight:700;font-size:15px">{title}</text>']
    for i, t in enumerate(lines):
        p.append(f'<text class="s" x="{cx}" y="{y+62+dy+i*14.5}" text-anchor="middle" style="font-size:11px">{t}</text>')
    return "".join(p)


def ways_in(p, w, ends, subs):
    p.append('<text class="k" x="0" y="96">WAYS IN</text>')
    for i, (n, s) in enumerate(zip(["Target portal", "Emails", "FacilIT"], subs)):
        y = 110 + i * 82
        p.append(box(0, y, w, 60, n, s))
        cx = (w + ends[3]) / 2  # control points between the two ends, so the arrowhead points forward
        p.append(line(f"M{w},{y+30} C{cx},{y+30} {cx},{ends[i]} {ends[3]},{ends[i]}"))


def mid_arrows(p, segs):
    """Short arrowhead-only segments that sit mid-line, so a feedback path reads in its direction."""
    for d in segs:
        p.append(line(d))


def svg_recommended():
    p = [ARROW]
    ways_in(p, 170, [190, 220, 250, 248], ["Their format, their rules.", "Starbucks stores, other clients.", "Smaller clients."])
    mid = len(p)  # everything after the ways in shifts left 20 to make room on the right
    p.append(cylinder(270, 148, 210, 144, "Job records", ["One record per request.", "Contract guardrails added.",
                      "Structured data for analysis.", "Maintains record state", "and makes visible for humans."], 360, dy=8, ty=184))
    # additional approvals: out of the record's top, back in, then on to dispatch (dotted inside, John 2026-11-13)
    p.append(box(270, 62, 175, 50, "Additional approvals", "Client sign-off, over a cap."))
    p.append(line("M300,140 V114"))
    p.append(line("M410,112 V140"))
    p.append(line("M410,141 V168 H478", dash=True))
    # inside the record: updates enter, billing exits (a gap where the approval path crosses)
    p.append(line("M458,137 V162 M458,174 V262 H478", dash=True))
    # feedback that needs approval goes straight back out to additional approvals (John, 2026-11-13)
    p.append(line("M458,202 H300 V140", dash=True, end=False))  # joins the solid arrow; one arrowhead only
    p.append(store(295, 378, 160, 54, "Contracts", "Maintained elsewhere, for now.", False))
    p.append(line("M375,378 V306"))
    p.append('<text class="e" x="384" y="340">Checked before</text><text class="e" x="384" y="354">work assigned.</text>')
    p.append(line("M480,168 H525 V130 H578"))
    p.append(box(580, 100, 160, 60, "Dispatch", "People, parts, routes."))
    p.append(line("M740,130 H788"))
    p.append(box(790, 100, 160, 60, "Onsite", "Tech analysis, repair."))
    p.append(line("M870,100 V40 H458 V136"))
    mid_arrows(p, ["M870,76 V66", "M775,40 H765", "M565,40 H555"])
    p.append('<path d="M660,100 V70 V40" fill="none" stroke="#444" stroke-width="1.3" marker-mid="url(#ar)"/>')
    p.append('<text class="e" x="645" y="32" text-anchor="middle">Updates the record.</text>')
    p.append(line("M480,262 H538"))
    p.append('<text class="e" x="487" y="254">On <tspan style="font-weight:700;font-style:normal;fill:#1c1b19">Close</tspan>.</text>')
    p.append(box(540, 232, 120, 60, "Billing", "Matched to the job."))
    p.append(line("M660,262 H683"))
    p.append(stack(685, 232, 155, 60, 6, "#fff", "#cfc9bf"))
    p.append(box(685, 232, 155, 60, "Invoicing", ["Multiple client formats,", "from the contract."]))
    # contracts also feed invoicing: each client's format, read-only
    p.append(line("M455,405 H762 V294"))
    p.append('<text class="e" x="560" y="398">Client specific invoice templating.</text>')
    p.append(line("M840,262 H863"))
    p.append(stack(865, 232, 105, 60, 6, "#fff", "#cfc9bf"))
    p.append(box(865, 232, 105, 60, "Collections", "Normal aging."))  # no disputes: the record prevents disputable work
    # humans in the loop on the system steps (decided earlier: the coordinator owns the request; people review and
    # override anything but the rails; billing sees only what fails the check)
    p.append(human(280, 294, "Coordinator"))
    p.append(human(318, 106, "Client"))
    p.append(human(650, 150, "Dispatcher"))
    p.append(human(880, 150, "Tech"))
    p.append(human(560, 290, "Controller"))
    p.append(human(772, 290, "Controller"))  # invoicing, right of the contracts arrow
    p.append(human(872, 290, "Controller"))
    p[mid:] = ['<g transform="translate(-20,0)">'] + p[mid:] + ['</g>']
    p.append(human(0, 352, "Role"))
    p.append('<text class="e" x="64" y="366">Human review and decision points.</text>')
    p.append('<rect x="0" y="382" width="26" height="16" rx="3" fill="#fff" stroke="#9a968f" stroke-width="1.2"/>'
             '<rect x="0" y="382" width="4" height="16" fill="#F7941E"/><text class="e" x="34" y="394">Step in the system.</text>')
    return f'<svg class="fig" viewBox="-2 -2 962 440" xmlns="http://www.w3.org/2000/svg" style="width:9.5in;margin-top:22px">{"".join(p)}</svg>'


def svg_current():
    """Today, from round 4: coordinators re-key and update by hand; the tech texts Tony; Tony updates the record;
    Marcee reconciles finished work with contracts and PO numbers before invoicing. No contract reaches the record."""
    p = [ARROW]
    ways_in(p, 150, [140, 222, 304, 178], ["Their format, their rules.", "Stores, other clients.", "Smaller clients."])
    p.append(manual(180, 110, 120, 224, "Coordinators", ["Re-key every", "request.", "", "Update the", "record.", "", "Chase approvals."]))
    p.append(line("M300,222 H328"))
    p.append(cylinder(330, 148, 160, 144, "Job records", ["One notes field.", "Detail lost", "in the handling.",
                      "No contract guardrails.", "State seen by no one."], 403))
    # approvals today: out of the record to the coordinators, who chase the approval, then back into the record
    p.append(line("M350,140 V90 H270 V108"))
    p.append('<text class="e" x="278" y="84">Needs approval.</text>')
    p.append(line("M220,110 V72"))
    p.append(box(180, 22, 175, 48, "Additional approvals", "Often chased after the work."))
    p.append(line("M355,46 H440 V140"))
    p.append(line("M440,158 V168 H488", dash=True))
    p.append(line("M478,152 V162 M478,174 V262 H488", dash=True))
    p.append(line("M490,168 H520 V130 H558"))
    p.append(manual(560, 92, 165, 76, "Dispatch: Tony", "One person, his own phone."))
    p.append(line("M725,118 H788"))
    p.append(box(790, 100, 160, 60, "Onsite", "Tech analysis, repair."))
    p.append(human(897, 90, "Tech"))  # human in the loop (John, 2026-11-13)
    p.append(line("M790,145 H727"))
    p.append('<text class="e" x="757" y="180" text-anchor="middle" style="fill:#9a5a00">Texts Tony from a personal phone.</text>')
    p.append(line("M642,92 V40 H478 V136"))
    mid_arrows(p, ["M642,76 V66", "M570,40 H560"])
    p.append('<text class="e" x="560" y="32" text-anchor="middle" style="fill:#9a5a00">Tony updates the record by hand.</text>')
    p.append(line("M490,262 H531"))
    p.append('<text class="e" x="493" y="255" style="font-size:10px">By hand.</text>')
    p.append(manual(533, 220, 134, 84, "Billing: Marcee", ["Reconciles finished", "work to contracts,", "PO numbers."]))
    p.append(line("M667,262 H685"))
    p.append(stack(687, 220, 145, 84, 14, "#eadbc4", "#1c1b19"))
    p.append(manual(687, 220, 145, 84, "Invoicing: Marcee", ["Multiple client", "formats, each", "by hand."]))
    p.append(line("M840,262 H853"))
    p.append(stack(855, 228, 92, 70, 6, "#fff", "#cfc9bf"))
    p.append(box(855, 228, 92, 70, "Collections", ["Normal", "aging."]))
    # disputes, by hand: back to the contracts, then to the coordinators and the approvals chase (John, 2026-11-13)
    p.append(line("M900,298 V326"))
    p.append(manual(838, 328, 117, 92, "Disputes", ["Marcee chases.", "$80K–$200K a year", "written off."]))
    p.append(line("M838,395 H752"))
    p.append(store(560, 378, 190, 54, "Contracts, POs", "Files, Sheets, tribal knowledge.", True))
    p.append(line("M596,378 V306"))
    p.append(line("M730,378 V306"))
    p.append('<text class="e" x="663" y="370" text-anchor="middle" style="fill:#9a5a00">After work complete.</text>')
    p.append(line("M560,405 H520 V345 H240 V337"))
    p.append('<text class="e" x="334" y="339" style="fill:#9a5a00">Rework: back to the coordinators.</text>')
    p.append(human(0, 358, "Role"))
    p.append('<text class="e" x="64" y="372">Human review and decision points.</text>')
    p.append('<rect x="0" y="386" width="26" height="16" rx="6" fill="#eadbc4" stroke="#1c1b19" stroke-width="1.4"/>'
             '<text class="e" x="34" y="398">Manual junction: Human makes multiple system decisions.</text>')
    p.append('<rect x="0" y="410" width="26" height="16" rx="3" fill="#fff" stroke="#9a968f" stroke-width="1.2"/>'
             '<rect x="0" y="410" width="4" height="16" fill="#F7941E"/><text class="e" x="34" y="422">Step in the system.</text>')
    return f'<svg class="fig" viewBox="-2 -2 962 444" xmlns="http://www.w3.org/2000/svg" style="width:9.5in;margin-top:22px">{"".join(p)}</svg>'


LAND = """<style>
  .sheet{width:11in;height:8.5in;padding:0.55in 0.75in 0.45in;}
  @media print{@page{size:11in 8.5in;margin:0;}}
  .title{margin-top:20px;}
</style>"""

PAGES = [
    ("Recommended Request Flow",
     "Every request lands in one job record, which pulls its contract read-only and applies it to that request. When a "
     "job needs more approval, the record sends it out and takes it back before dispatch. Dispatch and onsite update the "
     "record, and only then does it move on to billing, invoicing and collections.", svg_recommended),
    ("Current Request Flow",
     "Today coordinators re-key every request and update the record by hand. The tech texts Tony from a personal phone, "
     "and Tony updates the record. No contract reaches the record, so Marcee reconciles finished work with contracts and "
     "PO numbers before she can invoice.", svg_current),
]
pdfs = []
with sync_playwright() as pw:
    b = pw.chromium.launch(); pg = b.new_page()
    for i, (title, dek, fig) in enumerate(PAGES, 1):
        src = HERE / f"_landscape-{i}.html"
        src.write_text(f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>OneFamilyServices: {title}</title>
<link rel="stylesheet" href="common.css"><link rel="stylesheet" href="components.css">{STYLE}{LAND}</head>
<body><div class="sheet">
{MASTHEAD}
<h1 class="title">{title}</h1>
<div class="meta">{META}</div>
<p class="dek">{dek}</p>
{fig()}
<div class="folio">{i} / {len(PAGES)}</div>
</div></body></html>
""")
        pg.goto(src.as_uri()); pg.wait_for_load_state("networkidle")
        pdfs.append(pg.pdf(width="11in", height="8.5in", print_background=True))
    b.close()
# The landscape pages alone for now (John, 2026-11-13); --with-rest puts them in front of the portrait deck.
rest = "--with-rest" in sys.argv
out = HERE.parent / ("jahnel-poc-flows.pdf" if rest else "jahnel-poc-understanding.pdf")
w = PdfWriter()
for pdf in [PdfReader(io.BytesIO(x)) for x in pdfs] + ([PdfReader(str(HERE.parent / "_portrait.pdf"))] if rest else []):
    for page in pdf.pages:
        w.add_page(page)
with open(out, "wb") as f:
    w.write(f)
print("wrote", out, len(w.pages), "pages")
