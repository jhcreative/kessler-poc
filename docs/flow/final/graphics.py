#!/usr/bin/env python3
"""The four graphic pages of the final presentation (2, 4, 6, 8), redrawn from the flows deck's drawings
(docs/flow/deck/understanding.py, John 2026-11-13) with the 2026-11-16 changes (plan §2, "Drawing rules"):
the gears numbered 1 to 7 to match page 5's table, the exports (client invoices, QuickBooks) outside the app, and
five views on page 8. Writes page-2/4/6/8.html here; assemble.py renders them with the hand-written text pages.

This script owns only the graphic pages. It never writes a text page (PP-11).

    python3 graphics.py && python3 assemble.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "deck"))
from build import MASTHEAD, STYLE, ARROW, line, store  # noqa: E402  (build.py renders only under __main__)

# ---- the drawings, carried over from understanding.py; changes are marked 2026-11-16 ----


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
           f'<text class="k" x="{x+20}" y="{y+20}" style="fill:#9a5a00;font-size:9px">BY HAND</text>',
           f'<text class="h" x="{x+20}" y="{top}" style="font-weight:700;font-size:14.5px">{name}</text>']
    for i, t in enumerate(subs):
        out.append(f'<text class="s" x="{x+20}" y="{top+17+i*14}" style="font-size:11px">{t}</text>')
    return "".join(out)


def cylinder(x, y, w, h, title, lines, cx, dy=0, ty=None):
    p = [f'<path d="M{x},{y} a{w/2},10 0 0 1 {w},0 V{y+h} a{w/2},10 0 0 1 {-w},0 Z" fill="#fdf1e1" stroke="#F7941E" stroke-width="1.8"/>',
         f'<path d="M{x},{y} a{w/2},10 0 0 0 {w},0" fill="none" stroke="#F7941E" stroke-width="1.8"/>',
         f'<text class="h" x="{cx}" y="{ty if ty else y+42+dy}" text-anchor="middle" style="font-weight:700;font-size:15px">{title}</text>']
    for i, t in enumerate(lines):
        p.append(f'<text class="s" x="{cx}" y="{y+62+dy+i*14.5}" text-anchor="middle" style="font-size:11px">{t}</text>')
    return "".join(p)


def ways_in(p, w, ends, subs):
    p.append('<text class="k" x="0" y="96">INCOMING REQUESTS</text>')
    for i, (n, s) in enumerate(zip(["Target portal", "Emails", "FacilIT"], subs)):
        y = 110 + i * 82
        p.append(box(0, y, w, 60, n, s))
        cx = (w + ends[3]) / 2  # control points between the two ends, so the arrowhead points forward
        p.append(line(f"M{w},{y+30} C{cx},{y+30} {cx},{ends[i]} {ends[3]},{ends[i]}"))


LEGEND = {
    "human": "Human review and decision points.",
    "manual": "Manual junction: Human makes multiple system decisions.",
    "step": "Step in the system.",
    "gear": "Automation or application benefit.",
    "screen": "View in the application.",
}


def legend(p, kinds, y=476):
    """The key: one row well below the drawing, each icon centred over its words, so the icons sit close together
    (John, 2026-11-13)."""
    x = 0
    for k in kinds:
        w = max(len(LEGEND[k]) * 5.0, 50)
        c = x + w / 2
        if k == "human":
            p.append(human(c - 22, y - 10, "Role"))
        elif k == "manual":
            p.append(f'<rect x="{c-13}" y="{y-8}" width="26" height="16" rx="6" fill="#eadbc4" stroke="#1c1b19" stroke-width="1.4"/>')
        elif k == "step":
            p.append(f'<rect x="{c-13}" y="{y-8}" width="26" height="16" rx="3" fill="#fff" stroke="#9a968f" stroke-width="1.2"/>'
                     f'<rect x="{c-13}" y="{y-8}" width="4" height="16" fill="#F7941E"/>')
        elif k == "screen":
            p.append(f'<rect x="{c-13}" y="{y-8}" width="26" height="16" fill="#f7ecdc" stroke="#1c1b19" stroke-width="1.6"/>')
        else:
            p.append(gear(c, y))
        p.append(f'<text class="e" x="{c}" y="{y+22}" text-anchor="middle">{LEGEND[k]}</text>')
        x += w + 26


def mid_arrows(p, segs):
    """Short arrowhead-only segments that sit mid-line, so a feedback path reads in its direction."""
    for d in segs:
        p.append(line(d))


def svg_recommended(overlay=None, under=None, kinds=None, top=None):
    p = [ARROW]
    if under:
        under(p)  # final coordinates, drawn first so the flow sits on top
    ways_in(p, 170, [190, 220, 250, 237], ["Their format, their rules.", "Starbucks stores, other clients.", "Client portal manager."])
    mid = len(p)  # everything after the ways in shifts left 20 to make room on the right
    p.append(cylinder(259.5, 141, 231, 158, "Job records", ["One record per request.", "Contract guardrails added.",
                      "Structured data for analysis.", "Maintains record state", "and makes visible for humans."], 360, dy=11, ty=188))
    # additional approvals: out of the record's top, back in, then on to dispatch (dotted inside, John 2026-11-13)
    p.append(box(270, 6, 175, 44, "Additional approvals", "Client sign-off, over a cap."))  # above the updates line
    p.append(line("M300,133 V52"))
    p.append(line("M410,50 V130"))
    p.append(line("M410,132 V168 H488", dash=True))
    # inside the record: updates enter, billing exits (a gap where the approval path crosses)
    p.append(line("M458,134 V162 M458,174 V262 H488", dash=True))
    # feedback that needs approval goes straight back out to additional approvals (John, 2026-11-13)
    p.append(line("M458,202 H300 V133", dash=True, end=False))  # joins the solid arrow; one arrowhead only
    p.append(store(295, 378, 160, 54, "Contracts", "Maintained elsewhere, for now.", False))
    p.append(line("M375,378 V312"))
    p.append('<text class="e" x="390" y="340">Checked before</text><text class="e" x="390" y="354">work assigned.</text>')
    p.append(line("M490,168 H525 V140 H578"))
    p.append(box(580, 110, 160, 60, "Dispatch", "People, parts, routes."))
    p.append(line("M740,140 H788"))
    p.append(box(790, 110, 160, 60, "Onsite", "Tech analysis, repair."))
    p.append(line("M870,110 V88 H458 V132"))  # lowered toward dispatch and onsite (John, 2026-11-13)
    mid_arrows(p, ["M870,103 V96", "M775,88 H765", "M565,88 H555"])
    p.append('<path d="M660,110 V99 V88" fill="none" stroke="#444" stroke-width="1.3" marker-mid="url(#ar)"/>')
    p.append('<text class="e" x="765" y="101" text-anchor="middle">Updates the record.</text>')
    p.append(line("M490,262 H538"))
    p.append('<text class="e" x="494" y="239" style="font-size:10px;paint-order:stroke;stroke:#fff;stroke-width:3px">On <tspan style="font-weight:700;font-style:normal;fill:#1c1b19">Close</tspan>.</text>')
    p.append(box(540, 220, 140, 84, "Billing", ["Accepted work", "pre-matched to client."]))
    p.append(line("M680,262 H698"))
    p.append(stack(700, 220, 145, 84, 6, "#fff", "#cfc9bf"))
    p.append(box(700, 220, 145, 84, "Invoicing", ["Multiple client formats,", "from the contract."]))
    # contracts also feed invoicing: each client's format, read-only
    p.append(line("M455,405 H706 V306"))  # 2026-11-17: enters invoicing at its lower left, clear of the exports
    p.append('<text class="e" x="490" y="398">Client specific invoice templating.</text>')
    p.append(stack(865, 220, 100, 84, 6, "#fff", "#cfc9bf"))
    p.append(box(865, 220, 100, 84, "Collections", "Normal aging."))  # no disputes: the record prevents disputable work
    # humans in the loop on the system steps (decided earlier: the coordinator owns the request; people review and
    # override anything but the rails; billing sees only what fails the check)
    p.append(human(385, 302, "Coordinator"))  # right of the contracts arrow
    p.append(human(318, 47, "Client"))
    p.append(human(650, 160, "Dispatcher"))
    p.append(human(880, 160, "Tech"))
    p.append(human(555, 296, "Controller"))
    p.append(human(752, 296, "Controller"))  # invoicing, right of the contracts arrow
    p.append(human(872, 296, "Controller"))
    p[mid:] = ['<g transform="translate(-20,0)">'] + p[mid:] + ['</g>']
    exports(p)  # 2026-11-16: the exports sit outside the app, like the ways in
    if overlay:
        overlay(p)  # final coordinates: after the group's -20 shift
    if top:
        top(p)  # final coordinates, over everything but the key
    legend(p, kinds or ["human", "step"] + (["gear"] if overlay else []))
    return f'<svg class="fig" viewBox="-2 -2 1092 504" xmlns="http://www.w3.org/2000/svg" style="width:9.5in;margin-top:8px">{"".join(p)}</svg>'


def svg_current():
    """Today, from round 4: coordinators re-key and update by hand; the tech texts Tony; Tony updates the record;
    Marcee reconciles finished work with contracts and PO numbers before invoicing. No contract reaches the record."""
    p = [ARROW]
    ways_in(p, 150, [140, 222, 304, 170], ["Their format, their rules.", "Stores, other clients.", "Client portal manager."])
    p.append(manual(172, 102, 146, 238, "Coordinators", ["Re-key every", "request.", "", "Update the", "record.", "", "Chase approvals."]))
    p.append(line("M318,222 H336"))
    # job records 10% smaller than page 2's: today's record is the smaller idea (John, 2026-11-13)
    p.append(cylinder(338, 155, 144, 130, "Job records", ["One notes field.", "Detail lost", "in the handling.",
                      "No contract guardrails.", "State seen by no one."], 410))
    # approvals today: out of the record to the coordinators, who chase the approval, then back into the record
    p.append(line("M350,150 V90 H270 V100"))
    p.append('<text class="e" x="356" y="110">Needs approval.</text>')
    p.append(line("M220,102 V72"))
    p.append(box(180, 22, 175, 48, "Additional approvals", "Often chased after the work."))
    p.append(line("M355,46 H440 V146"))
    p.append(line("M440,148 V168 H480", dash=True))
    p.append(line("M470,151 V162 M470,174 V262 H480", dash=True))
    p.append(line("M482,168 H515 V130 H550"))
    p.append(manual(552, 84, 180, 92, "Dispatch: Tony", "One person, his own phone."))
    p.append(line("M732,118 H788"))
    p.append(box(790, 110, 160, 60, "Onsite", "Tech analysis, repair."))
    p.append(human(880, 160, "Tech"))  # on the box's bottom edge, like every chip (John, 2026-11-17)
    p.append(line("M790,145 H734"))
    p.append('<text class="e" x="760" y="192" text-anchor="middle" style="fill:#9a5a00">Texts Tony from a personal phone.</text>')
    p.append(line("M642,84 V66 H470 V146"))  # lowered toward dispatch (John, 2026-11-13)
    mid_arrows(p, ["M570,66 H560"])
    p.append('<text class="e" x="560" y="58" text-anchor="middle" style="fill:#9a5a00">Tony updates the record by hand.</text>')
    # the record tells no one in real time, so Tony goes straight to the coordinators (John, 2026-11-13)
    p.append(line("M700,84 V12 H160 V120 H170"))
    mid_arrows(p, ["M700,50 V40", "M440,12 H430", "M160,64 V74"])
    p.append('<text class="e" x="362" y="26" style="fill:#9a5a00">Tony tells the</text>'
             '<text class="e" x="362" y="37" style="fill:#9a5a00">coordinators directly.</text>')
    p.append(line("M482,262 H528"))
    p.append('<text class="e" x="486" y="255" style="font-size:10px">By hand.</text>')
    p.append(manual(530, 212, 140, 100, "Billing: Marcee", ["Reconciles finished", "work to contracts,", "PO numbers."]))
    p.append(line("M670,262 H686"))
    p.append(stack(688, 212, 150, 100, 14, "#eadbc4", "#1c1b19"))
    p.append(manual(688, 212, 150, 100, "Invoicing: Marcee", ["Multiple client", "formats, each", "by hand."]))
    p.append(line("M846,262 H856"))
    p.append(stack(858, 228, 92, 70, 6, "#fff", "#cfc9bf"))
    p.append(box(858, 228, 92, 70, "Collections", ["Normal", "aging."]))
    # disputes, by hand: back to the contracts, then to the coordinators and the approvals chase (John, 2026-11-13)
    p.append(line("M904,298 V326"))
    p.append(manual(836, 328, 122, 100, "Disputes", ["Marcee chases.", "$80K–$200K a year", "written off."]))
    p.append(line("M836,395 H752"))
    p.append(store(560, 378, 190, 54, "Contracts, POs", "Files, Sheets, tribal knowledge.", True))
    p.append(line("M596,378 V314"))
    p.append(line("M730,378 V314"))
    p.append('<text class="e" x="663" y="370" text-anchor="middle" style="fill:#9a5a00">After work complete.</text>')
    p.append(line("M560,405 H520 V354 H240 V342"))
    p.append('<text class="e" x="334" y="349" style="fill:#9a5a00">Rework: back to the coordinators.</text>')
    legend(p, ["human", "manual", "step"])
    return f'<svg class="fig" viewBox="-2 -2 962 504" xmlns="http://www.w3.org/2000/svg" style="width:9.5in;margin-top:8px">{"".join(p)}</svg>'



def exports(p):
    """The end of the flow (John, 2026-11-17): invoicing drafts and exports to the clients' own systems and to
    QuickBooks. QuickBooks comes first after invoicing, and it feeds both the final phase, collections, and the
    company's accounting. Everything here but collections sits outside the app. Final coordinates."""
    p.append('<text class="k" x="692" y="420" text-anchor="end">OUTGOING</text>')
    p.append(stack(700, 386, 130, 56, 6, "#fff", "#cfc9bf"))
    p.append(box(700, 386, 130, 56, "Client systems", "Their invoice formats."))
    p.append(box(850, 386, 110, 56, "QuickBooks", "Ledger, aging."))
    p.append(box(985, 220, 100, 84, "Accounting", ["Company books."]))
    p.append(line("M818,304 V350", end=False))   # out of invoicing
    p.append(line("M818,350 H765 V384"))         # to the client systems
    p.append(line("M818,350 H880 V384"))         # to QuickBooks
    p.append(line("M960,414 H972 V262", end=False))  # QuickBooks feeds both
    p.append(line("M972,262 H948"))              # collections, the final phase
    p.append(line("M972,262 H983"))              # the company's accounting
    p.append('<circle cx="972" cy="262" r="3.2" fill="#444"/>')  # one source, two uses


def badge(cx, cy, n):
    """The gear's number, matching page 5's table (John, 2026-11-16): an orange disc at the gear's upper right, or its
    upper left where the caption sits on the right (6 and 7, by the exports)."""
    x, y = (cx - 10 if n in LEFT_BADGES else cx + 10), cy - 10
    return (f'<circle cx="{x}" cy="{y}" r="7.2" fill="#D07200" stroke="#fff" stroke-width="1.4"/>'
            f'<text x="{x}" y="{y+3.6}" text-anchor="middle" style="font-size:10px;font-weight:700;fill:#fff">{n}</text>')


def svg_opportunities():
    """Page 6: the recommended flow with its improvement opportunities on top, each gear numbered to page 5's table."""
    return svg_recommended(gears_overlay)


def svg_application():
    """Page 8: the five views laid over the recommended flow (John, 2026-11-16: five, not three). Four views tile the
    flow, edges touching; the overview is a frame around them, since it sees every job. The ways in, the contracts and
    the exports stay outside, at full strength. The gear numbers sit on top so they still track to page 5."""
    def views(p):
        (x0, y0, x1, y1), n, name = OVERVIEW
        p.append(f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="none" stroke="#1c1b19" '
                 f'stroke-width="2" stroke-dasharray="7 4"/>')
        for (a0, b0, a1, b1), fill, _, _ in SCREENS:
            p.append(f'<rect x="{a0}" y="{b0}" width="{a1-a0}" height="{b1-b0}" fill="{fill}" fill-opacity="0.88" '
                     f'stroke="#1c1b19" stroke-width="2"/>')
        for cx, cy, n_ in BADGES:
            p.append(gear(cx, cy) + badge(cx, cy, n_))
        for (cx, cy), (_, _, k, nm) in zip(LABELS, SCREENS):
            label(p, cx, cy, f"{k}  {nm}")
        label(p, x1 - 90, y0, f"{n}  {name}")
    return svg_recommended(None, top=views, kinds=["screen", "human", "step", "gear"])


def label(p, cx, cy, text):
    w = len(text) * 8.4 + 20
    p.append(f'<rect x="{cx-w/2}" y="{cy-15}" width="{w}" height="30" rx="6" fill="#fff" stroke="#1c1b19" stroke-width="1.6"/>'
             f'<text x="{cx}" y="{cy+5.5}" text-anchor="middle" style="font-size:16px;font-weight:700;fill:#1c1b19;'
             f'white-space:pre">{text}</text>')


# ((x0, y0, x1, y1), fill, number, name): the four tiled views, final coordinates; edges touch (2026-11-16: five views)
SCREENS = [
    ((188, 76, 510, 356), "#f7ecdc", "1", "Coordinator"),
    ((510, 76, 745, 196), "#eceae4", "2", "Dispatch"),
    ((745, 76, 952, 196), "#f3eee6", "3", "Tech"),
    ((510, 196, 952, 356), "#f1e6d4", "4", "Controller"),
]
OVERVIEW = ((180, 68, 958, 364), "5", "Overview")
# each label sits over its view's main step, so no step name shows half covered
LABELS = [(349, 216), (627, 134), (812, 132), (731, 276)]


def gears_overlay(p):
    for n, cx, cy, lines, anchor, tx, ty in GEARS:
        p.append(gear(cx, cy) + badge(cx, cy, n))
        for i, t in enumerate(lines):
            p.append(f'<text x="{tx}" y="{ty+i*10.8}" text-anchor="{anchor}" '
                     f'style="font-size:9.8px;font-weight:600;fill:#1c1b19;paint-order:stroke;stroke:#fff;stroke-width:3px">{t}</text>')


# (number, gear x, gear y, text lines, anchor, text x, text y): final coordinates on the recommended drawing.
# Numbers match page 5's table (John, 2026-11-16; renumbered 2026-11-17); the three ways in share number 1.
GEARS = [
    (1, 204, 165, [], "middle", 204, 0),   # Target portal
    (1, 204, 221, [], "middle", 204, 0),   # Emails
    (1, 204, 277, ["Auto draft job", "records from source."], "start", 194, 304),   # FacilIT; one caption for the column
    (2, 355, 346, ["Auto provide contract", "guardrails before work begins."], "end", 342, 344),
    (3, 552, 176, ["Recommended tech,", "with the reasons."], "start", 566, 194),
    (4, 505, 88, ["One way update flow keeps", "everyone on same page."], "middle", 494, 108),
    (5, 489, 262, ["Auto push", "to queue."], "middle", 489, 284),
    (6, 765, 368, ["Auto draft", "client invoices."], "start", 777, 366),
    (7, 880, 368, ["Auto export", "to QuickBooks."], "start", 892, 366),
]
LEFT_BADGES = {6, 7}
BADGES = [(cx, cy, n) for n, cx, cy, *_ in GEARS]


def gear(cx, cy, r=7.5):
    """A small black gear: eight teeth, a body and a white hub."""
    teeth = "".join(f'<rect x="-2.3" y="{-r-3.2}" width="4.6" height="4.6" rx="0.8" transform="rotate({a})"/>'
                    for a in range(0, 360, 45))
    return (f'<g transform="translate({cx},{cy})" fill="#1c1b19">{teeth}<circle r="{r}"/>'
            f'<circle r="{r*0.38}" fill="#fff"/></g>')


# ---- the pages ----
META = ('Proof of Concept<span class="dot">&bull;</span>OneFamilyServices'
        '<span class="dot">&bull;</span>November 16, 2026')
LOGO = MASTHEAD[MASTHEAD.index('xlink:href="data:'):].split('"')[1]
HEAD = MASTHEAD.replace(LOGO, "jhc-logo.png")

PAGES = {
    2: ("Current Request Flow",
        "Current request flow requires complex human facilitation at multiple points, including manual data entry, "
        "professional analysis, decision making and notification responsibilities all in a single human role, creating "
        "concerns for efficient scaling and expansion.", svg_current),
    4: ("Recommended Request Flow",
        "Recommended request flow automates the redundant parts of each human role, including data entry, contract "
        "checks and notifications, and streamlines communication through one shared record, so the same people make "
        "better decisions faster as the volume of business grows.", svg_recommended),
    6: ("Flow Improvement Opportunities",
        "Each numbered gear is an efficiency from the table on page 5. Each one works on its own; together they "
        "centralize the source of truth for every request, so people decide with every fact in view.",
        svg_opportunities),
    8: ("Application Surface",
        "Five views work from the one record: <b>1</b> coordinator, <b>2</b> dispatch, <b>3</b> the tech's phone, "
        "<b>4</b> controller, and <b>5</b> the overview around them all. Requests come in from the left; invoices go "
        "out to client systems and QuickBooks, which feeds collections and the company books. All stay outside the app.", svg_application),
}


def main():
    for i, (title, dek, fig) in PAGES.items():
        (HERE / f"page-{i}.html").write_text(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>OneFamilyServices: {title}</title>
<link rel="stylesheet" href="../deck/common.css"><link rel="stylesheet" href="../deck/components.css">
<link rel="stylesheet" href="final.css">{STYLE}</head>
<body><div class="sheet">
{HEAD}
<h1 class="title">{title}</h1>
<div class="meta">{META}</div>
<p class="dek">{dek}</p>
{fig()}
<div class="folio">{i} / 9</div>
</div></body></html>
""")
    print("wrote pages", ", ".join(map(str, PAGES)))


if __name__ == "__main__":
    main()
