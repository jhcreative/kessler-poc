#!/usr/bin/env python3
"""Build the flows deck: the decision first, then flow 1 and flow 2, drawn from docs/flow/*.yaml.

Writes page-N.html beside this file on the JHC brand sheet (writer-brand-kit), then the assembler makes the PDF:
    python3 build.py && python3 <kit>/assemble_report_pdf.py . -o ../jahnel-poc-flows-2026-11-12.pdf
The diagrams are hand-placed SVG; the yaml files are the source of truth for every word in them.
"""
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = Path.home() / "jhc/jhc-agency/skills/product-ops/writer-brand-kit"
TEMPLATE = Path.home() / "jhc/jhc-agency/skills/product-ops/proposal-writer/assets/page-one-template.html"

src = TEMPLATE.read_text()
MASTHEAD = src[src.index('<div class="masthead">'):src.index('<h1 class="title">')].strip()
META = 'Discovery Report<span class="dot">&bull;</span>OneFamilyServices<span class="dot">&bull;</span>November 12, 2026'

STYLE = """
<style>
  .dek{font-size:11.5pt;margin:10px 0 0;}
  svg.fig{display:block;width:6.8in;height:auto;margin:14px 0 0;}
  svg.fig text{font-family:'Fira Sans',sans-serif;fill:#1c1b19;}
  svg.fig .h{font-weight:700;font-size:13.5px;}
  svg.fig .s{font-size:11.5px;fill:#3a382f;}
  svg.fig .k{font-weight:600;font-size:10px;letter-spacing:.08em;fill:#6f6c66;}
  svg.fig .n{font-weight:700;font-size:13.5px;fill:#D07200;}
  svg.fig .e{font-size:10.5px;fill:#6f6c66;font-style:italic;}
  .two{display:flex;gap:26px;}
  .two > div{flex:1;}
  .two h2{margin-top:18px;}
  table.flow td{font-size:9.8pt;line-height:1.36;padding:8px 9px;}
  table.flow td.b{font-family:'Fira Sans',sans-serif;font-weight:600;font-size:9.6pt;white-space:nowrap;}
  table.flow td.b span{display:block;font-weight:400;color:var(--muted);font-size:8.4pt;}
  .answer{margin:14px 0 0;}
  .answer p{font-size:10.6pt;}
  .src{font-family:'Fira Sans',sans-serif;font-size:8.2pt;color:var(--faint);margin:10px 0 0;}
  ul li{font-size:11pt;margin-bottom:4px;}
</style>"""

ARROW = """<defs>
  <marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0,0 L10,5 L0,10 z" fill="#1c1b19"/></marker>
  <marker id="ao" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0,0 L10,5 L0,10 z" fill="#D07200"/></marker>
</defs>"""


def block(x, y, w, h, steps, name, lines, fill="#fff"):
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{fill}" stroke="#cfc9bf" stroke-width="1.2"/>',
           f'<rect x="{x}" y="{y}" width="5" height="{h}" rx="2" fill="#F7941E"/>',
           f'<text x="{x+16}" y="{y+22}"><tspan class="n">{steps}</tspan><tspan class="h" dx="8">{name}</tspan></text>']
    for i, (cls, t) in enumerate(lines):
        out.append(f'<text class="{cls}" x="{x+16}" y="{y+42+i*17}">{t}</text>')
    return "\n".join(out)


def pill(x, y, w, h, t, cls="s", stroke="#cfc9bf", fill="#faf8f4", dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{min(h/2,6)}" fill="{fill}" stroke="{stroke}" stroke-width="1.1"{d}/>'
            f'<text class="{cls}" x="{x+w/2}" y="{y+h/2+4}" text-anchor="middle">{t}</text>')


def line(d, orange=False, dash=False, end=True):
    c = "#D07200" if orange else "#1c1b19"
    m = f' marker-end="url(#{"ao" if orange else "ar"})"' if end else ""
    da = ' stroke-dasharray="5 4"' if dash else ""
    return f'<path d="{d}" fill="none" stroke="{c}" stroke-width="1.3"{da}{m}/>'


# ---------- Page 1: the decision ----------
def harness_svg():
    p = [ARROW]
    p.append('<text class="k" x="0" y="12">WAYS IN</text><text class="k" x="680" y="12" text-anchor="end">SYSTEMS AND THE FIELD</text>')
    left = [("Target portal", "their format, their rules"), ("Store emails", "Starbucks"),
            ("Client emails", "and attachments"), ("FacilIT", "smaller clients")]
    right = [("FieldDesk", "today's records"), ("QuickBooks", "invoices and aging"),
             ("Samsara", "fleet and drivers"), ("Field app", "ours, for every tech")]
    cy = 175
    for i, (t, sub) in enumerate(left):
        y = 26 + i * 76
        p.append(f'<rect x="0" y="{y}" width="168" height="58" rx="5" fill="#faf8f4" stroke="#cfc9bf" stroke-width="1.1"/>')
        p.append(f'<text class="h" x="14" y="{y+25}">{t}</text><text class="s" x="14" y="{y+44}">{sub}</text>')
        p.append(line(f"M168,{y+29} C205,{y+29} 200,{cy-36+i*24} 228,{cy-36+i*24}", end=False))
        p.append(f'<rect x="226" y="{cy-41+i*24}" width="10" height="10" rx="2" fill="#F7941E"/>')
    for i, (t, sub) in enumerate(right):
        y = 26 + i * 76
        ours = t == "Field app"
        p.append(f'<rect x="512" y="{y}" width="168" height="58" rx="5" fill="{"#1c1b19" if ours else "#faf8f4"}" stroke="{"#1c1b19" if ours else "#cfc9bf"}" stroke-width="1.1"/>')
        col = ' style="fill:#fff"' if ours else ""
        p.append(f'<text class="h" x="526" y="{y+25}"{col}>{t}</text><text class="s" x="526" y="{y+44}"{col}>{sub}</text>')
        p.append(line(f"M512,{y+29} C475,{y+29} 480,{cy-36+i*24} 452,{cy-36+i*24}", end=False))
        p.append(f'<rect x="444" y="{cy-41+i*24}" width="10" height="10" rx="2" fill="#F7941E"/>')
    p.append('<rect x="236" y="96" width="208" height="160" rx="7" fill="#fdf1e1" stroke="#F7941E" stroke-width="1.6"/>')
    for i, (cls, t) in enumerate([("h", "Our job record"), ("s", "identity, working fields,"), ("s", "approval, state"),
                                  ("h", "Each client's rules"), ("s", "caps, approval rules,"), ("s", "contract terms")]):
        p.append(f'<text class="{cls}" x="340" y="{124+i*21+(10 if i>2 else 0)}" text-anchor="middle">{t}</text>')
    p.append('<rect x="236" y="300" width="10" height="10" rx="2" fill="#F7941E"/><text class="e" x="254" y="309">adapter: one per way in or out</text>')
    return f'<svg class="fig" viewBox="-2 -2 684 320" xmlns="http://www.w3.org/2000/svg">{"".join(p)}</svg>'


PAGE1 = f"""
<h1 class="title">How We're Building the POC</h1>
<div class="meta">{META}</div>
<p class="dek">We build a harness: our own job record and each client's rules in the middle, with an adapter for every
way in and out. FacilIT is one of those adapters, not the core.</p>
{harness_svg()}
<div class="two">
<div>
<h2>Why</h2>
<ul>
<li>Target sets its own format; it won't bend to FacilIT's, or to ours.</li>
<li>One rule, such as Target's $25K cap, reaches every job, whatever door it came through.</li>
<li>A new client is a new adapter.</li>
<li>No paid subscription becomes the system the company can't leave.</li>
</ul>
</div>
<div>
<h2>What it costs</h2>
<ul>
<li>We own more: the record, the rules, every adapter.</li>
<li>Each feature FacilIT already has (signatures, approvals) gets its own call: use theirs, or build ours.</li>
<li>One field app, ours, for every tech and every job.</li>
<li>If FacilIT's edition already covers most of this, we'd be rebuilding paid work. A later round asks which edition they have.</li>
</ul>
</div>
</div>
"""

# ---------- Page 2: flow 1 diagram ----------
def flow1_svg():
    p = [ARROW]
    for i, t in enumerate(["Target portal", "Store emails", "Client emails", "FacilIT"]):
        x = 70 + i * 98
        p.append(pill(x, 0, 88, 28, t))
        p.append(line(f"M{x+44},28 V58"))
    W = 380
    blocks = [
        (60, "1–2", "COORDINATOR", [("s", "Person: the coordinator, who owns the request until close"),
                                   ("s", "System: turns every way in into one job record"),
                                   ("s", "System: attaches the contract: caps, approval rules, terms")]),
        (210, "3", "ESTIMATION", [("s", "Person: the tech confirms or denies, onsite"),
                                 ("s", "System: predicts a range of values from like jobs"),
                                 ("s", "System: records the difference when a person overrides")]),
        (360, "4", "DISPATCH", [("s", "Person: the dispatcher"),
                               ("s", "System: assigns by location, weather, capacity, skills,"),
                               ("s", "trade licenses by state; stages the likely parts")]),
        (510, "5", "TECH ONSITE", [("s", "Person: the tech, in one field app for every job"),
                                  ("s", "System: captures what the site really needs"),
                                  ("s", "Reviews and overrides anything, except the rails")]),
    ]
    for y, n, name, lines in blocks:
        p.append(block(70, y, W, 100, n, name, lines))
    p.append('<rect x="262" y="518" width="178" height="20" rx="3" fill="#fdf1e1" stroke="#F7941E" stroke-width="1"/>'
             '<text class="s" x="351" y="532" text-anchor="middle" style="font-weight:600;fill:#9a5a00">Rails: price caps, contract terms</text>')
    for y0, t in [(160, "qualified request, with its contract"), (310, "enriched request, with a predicted range"),
                  (460, "assigned job, likely parts staged")]:
        p.append(line(f"M150,{y0} V{y0+48}"))
        p.append(f'<text class="e" x="160" y="{y0+29}">{t}</text>')
    # coordinator lane
    p.append('<rect x="0" y="60" width="22" height="550" rx="3" fill="#fdf1e1"/>'
             '<text class="k" transform="translate(15,335) rotate(-90)" text-anchor="middle">THE COORDINATOR OWNS IT UNTIL CLOSE</text>')
    # learning loop
    p.append(line("M70,590 H44 V262 H68"))
    p.append('<text class="e" transform="translate(39,426) rotate(-90)" text-anchor="middle">learning: a person reviews it first</text>')
    # approval-required event
    p.append('<rect x="500" y="505" width="180" height="110" rx="6" fill="#fdf1e1" stroke="#D07200" stroke-width="1.6"/>')
    for i, (cls, t) in enumerate([("k", "EVENT, IN REAL TIME"), ("h", "Approval required"),
                                  ("s", "over a cap, or any rule"), ("s", "that fires in the field")]):
        p.append(f'<text class="{cls}" x="514" y="{528+i*19}">{t}</text>')
    p.append(line("M450,560 H498", orange=True))
    p.append(line("M560,505 V410 H452", orange=True))
    p.append('<text class="e" x="462" y="402" style="fill:#9a5a00">dispatch re-plans now</text>')
    p.append(line("M650,505 V110 H452", orange=True))
    p.append('<text class="e" x="462" y="102" style="fill:#9a5a00">coordinator starts approval now</text>')
    # handoff
    p.append(line("M260,610 V648"))
    p.append(pill(140, 650, 240, 34, "Flow 2: close to cash, steps 6–9", cls="h", dash="5 4", fill="#fff"))
    return f'<svg class="fig" viewBox="-2 -2 684 694" xmlns="http://www.w3.org/2000/svg">{"".join(p)}</svg>'


PAGE2 = f"""
<h1 class="title">Flow 1: Request to Onsite</h1>
<div class="meta">{META}</div>
<p class="dek">Steps 1 to 5. Every request becomes one job record that carries its contract to every person before the
work. Each human decision teaches the system.</p>
{flow1_svg()}
"""

# ---------- Page 3: flow 1 by block ----------
PAGE3 = f"""
<h1 class="title">Flow 1, Block by Block</h1>
<div class="meta">{META}</div>
<table class="flow">
<thead><tr><th>Block</th><th>Comes in</th><th>The system</th><th>Goes out</th></tr></thead>
<tbody>
<tr><td class="b">Coordinator<span>steps 1–2</span></td>
<td>Target's portal, Starbucks store emails, other clients' emails and attachments, FacilIT</td>
<td>Wrangles every intake type into one job record; attaches the contract by lookup, FacilIT included</td>
<td>Qualified request: identity fixed, contract attached</td></tr>
<tr><td class="b">Estimation<span>step 3</span></td>
<td>The qualified request; history of like jobs</td>
<td>Predicts a range of values; keeps the history; records every override</td>
<td>Enriched request with a predicted range</td></tr>
<tr><td class="b">Dispatch<span>step 4</span></td>
<td>The enriched request; Samsara fleet data; weather; each tech's skills and licenses in seven states</td>
<td>Optimizes assignments; prepares for likely parts; vendor and support work</td>
<td>Assigned job, likely parts staged</td></tr>
<tr><td class="b">Tech onsite<span>step 5</span></td>
<td>The assigned job, in one field app</td>
<td>Captures what reality says, against what was predicted</td>
<td>Job ready to close, to flow 2</td></tr>
</tbody>
</table>
<div class="answer"><p class="q">The certain win: approval in real time</p>
<p>When a job in the field needs client approval, over a cap or any rule that fires, the job updates at once. Dispatch
re-plans the allocation, and the coordinator starts the approval right away instead of chasing it after the work. Today
the chase comes after, and the dispute follows.</p></div>
<div class="two">
<div>
<h2>People decide</h2>
<ul>
<li>A person can review and override anything in the field.</li>
<li>Every confirm, deny and override is recorded.</li>
<li>A person reviews what the system learned before it changes future predictions.</li>
</ul>
</div>
<div>
<h2>Rails nobody overrides</h2>
<ul>
<li>Price caps.</li>
<li>Every other stipulation in the client's contract.</li>
</ul>
<h2>Still open</h2>
<ul>
<li>Which contract terms the record must carry first.</li>
<li>What makes two jobs "like" for the predicted range.</li>
</ul>
</div>
</div>
<p class="src">Source: docs/flow/request-to-onsite.yaml, draft 2.</p>
"""

# ---------- Page 4: flow 2 diagram ----------
def flow2_svg():
    p = [ARROW]
    p.append(pill(70, 0, 380, 32, "From flow 1: job ready to close, approvals on record", cls="s", dash="5 4", fill="#fff"))
    p.append(pill(500, 0, 180, 32, "Flow 1: the coordinator", cls="s", dash="5 4", fill="#fff"))
    p.append(line("M150,32 V58"))
    W = 380
    blocks = [
        (60, "6", "CLOSE", [("s", "Today: work complete in FieldDesk, which triggers billing"),
                           ("s", "Today: the client's local rep signs in the field"),
                           ("s", "Proposed: no close without the signature, or a reason")]),
        (210, "7", "BILLING", [("s", "Today: one person matches each job by hand to the"),
                              ("s", "contract, the PO and the signature"),
                              ("s", "Proposed: the system matches; she sees only what fails")]),
        (360, "8", "INVOICING", [("s", "Today: keyed into QuickBooks, then sent in each client's"),
                                ("s", "format; about a dozen are strict"),
                                ("s", "Proposed: one invoice, written out per client's adapter")]),
        (510, "9", "COLLECTIONS", [("s", "Today: QuickBooks aging and a few spreadsheets"),
                                  ("s", "Proposed: every dispute recorded against its job,"),
                                  ("s", "with the rule that should have fired")]),
    ]
    for y, n, name, lines in blocks:
        p.append(block(70, y, W, 100, n, name, lines))
    for y0, t in [(160, "closed job, with the signature"), (310, "job that passes every check"),
                  (460, "invoice in the client's format")]:
        p.append(line(f"M150,{y0} V{y0+48}"))
        p.append(f'<text class="e" x="160" y="{y0+29}">{t}</text>')
    # check-failed event
    p.append('<rect x="500" y="205" width="180" height="110" rx="6" fill="#fdf1e1" stroke="#D07200" stroke-width="1.6" stroke-dasharray="5 4"/>')
    for i, (cls, t) in enumerate([("k", "EVENT, PROPOSED"), ("h", "Check failed"),
                                  ("s", "no approval on record,"), ("s", "no signature, no PO")]):
        p.append(f'<text class="{cls}" x="514" y="{228+i*19}">{t}</text>')
    p.append(line("M450,260 H498", orange=True))
    p.append(line("M590,205 V34", orange=True))
    p.append('<text class="e" x="600" y="110" style="fill:#9a5a00">invoice held;</text>')
    p.append('<text class="e" x="600" y="125" style="fill:#9a5a00">coordinator told</text>')
    p.append('<text class="e" x="600" y="140" style="fill:#9a5a00">what\'s missing</text>')
    # learning loop
    p.append(line("M70,590 H40 V16 H68"))
    p.append('<text class="e" transform="translate(34,300) rotate(-90)" text-anchor="middle">learning: each dispute and its cause sharpen the rules; a person reviews</text>')
    p.append(line("M260,610 V648"))
    p.append(pill(140, 650, 240, 34, "Paid, or a dispute tied to its cause", cls="h", fill="#fff"))
    return f'<svg class="fig" viewBox="-2 -2 684 694" xmlns="http://www.w3.org/2000/svg">{"".join(p)}</svg>'


PAGE4 = f"""
<h1 class="title">Flow 2: Close to Cash</h1>
<div class="meta">{META}</div>
<p class="dek">Steps 6 to 9. The $80K to $200K a year in disputes starts before the work. This flow checks the record
before an invoice leaves. Today's steps are from discovery; what's marked proposed waits on Dana's answers.</p>
{flow2_svg()}
"""

# ---------- Page 5: flow 2 today and proposed ----------
PAGE5 = f"""
<h1 class="title">Flow 2, Today and Proposed</h1>
<div class="meta">{META}</div>
<table class="flow">
<thead><tr><th>Step</th><th>Today</th><th>Proposed</th></tr></thead>
<tbody>
<tr><td class="b">Close<span>step 6</span></td>
<td>Work complete is registered in FieldDesk, which somehow triggers billing. The client's local rep signs off in the field.</td>
<td>The field app closes a job only with the signature, or with the reason it's missing. Closing puts the job into billing; nobody has to go and get it.</td></tr>
<tr><td class="b">Billing<span>step 7</span></td>
<td>One person pulls completed work from FieldDesk, timing varying with volume, and matches it by hand to the contract, the PO and the signature.</td>
<td>The system makes the match: approval on record when a rule required it, signature, PO, amount within the cap. She sees only what fails.</td></tr>
<tr><td class="b">Invoicing<span>step 8</span></td>
<td>The same person keys each invoice into QuickBooks, then sends it in the client's format. About a dozen clients set strict ones.</td>
<td>One invoice from the job record, written out by each client's adapter, with the approval and signature attached. QuickBooks gets it without re-keying.</td></tr>
<tr><td class="b">Collections<span>step 9</span></td>
<td>QuickBooks aging and a few spreadsheets. The same person is the only one who enforces; when she's out, little happens.</td>
<td>Every dispute is recorded against its job, with the rule that should have fired, and fed back to flow 1.</td></tr>
</tbody>
</table>
<div class="answer"><p class="q">Why this flow matters</p>
<p>Aging isn't the concern; disputes are. Once the work is done, the company invoices even when the signature is missing
or the contract is vague, because it's the only way to get paid. The check before the invoice makes that gap visible
while it can still be closed.</p></div>
<h2>Still open</h2>
<ul>
<li>How a close in FieldDesk triggers billing today, and whether its data can get out.</li>
<li>Each strict-format client's invoice rules: Target, CVS, Walgreens, Wegmans, ALDI.</li>
<li>How the disputes split: no approval on record, a missing signature, a vague contract.</li>
</ul>
<p class="src">Source: docs/flow/close-to-cash.yaml, draft 1.</p>
"""

PAGES = [PAGE1, PAGE2, PAGE3, PAGE4, PAGE5]


def main():
    for f in ("common.css", "components.css"):
        shutil.copy(KIT / f, HERE / f)
    for old in HERE.glob("page-*.html"):
        old.unlink()
    n = len(PAGES)
    for i, body in enumerate(PAGES, 1):
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>OneFamilyServices flows, page {i}</title>
<link rel="stylesheet" href="common.css">
<link rel="stylesheet" href="components.css">
{STYLE}
</head>
<body>
<div class="sheet">
{MASTHEAD}
{body}
<div class="folio">{i} / {n}</div>
</div>
</body>
</html>
"""
        (HERE / f"page-{i}.html").write_text(html)
    print(f"wrote {n} pages")


if __name__ == "__main__":
    main()
