# POC plan walkthrough with John (Angela runs it, about 20 minutes)

Plan: `2026-11-13-poc-plan.md`. Deck: `opportunities/onefamilyservices-flows-and-views-2026-11-13.pdf`.

## Order

1. **Two minutes, the story.** The four pages are problem, solution, what to automate and blueprint (plan §1). Does the
   demo script (§11) tell the story you want Ann-Marie to see?
2. **Five minutes, the goals.** Read the acceptance table (§2). Anything missing, or too much for Monday?
3. **Three minutes, the architecture.** Commands in, events out, websocket, and replay on reconnect (§4). Any concern?
4. **Ten minutes, the gaps.** The table below. Each one has a default, so a missing answer never blocks the build.
5. **Approve the plan (T3)**, and the cut line (§10).

## Questions

| # | Question | Recommendation | Answer |
|---|---|---|---|
| Q1 | Host the POC on a fresh OVH VPS-1 ($5.75/mo), or as a third site on the John-account box with Jessica and Logan? | Fresh VPS-1: a demo reset never touches a client | |
| Q2 | Which URL? | `poc.johnhiemstra.com` (or `onefamily.jhcreative…`) | |
| Q3 | May the intake drafter call Claude, or is rule-based drafting enough for Monday? | Rule-based for Monday, with Claude behind a flag if you say yes | |
| Q4 | Use real chain names (Target, Starbucks) as Dana did, or fictional ones? | Fictional on screen; say "a national retailer" out loud | |
| Q5 | Use Dana's staff names (Tony, Marcee) in the app, or role names? | Role names plus fictional people: the app is for any client | |
| Q6 | Has Neale confirmed the format, the recipients and what "deployed" means for step 5? | Plan for a live URL plus a repo walkthrough | |
| Q7 | Tailor: may the POC code live as an instance-local module (not in Tailor core)? | Yes. Cesar checks the seam Saturday morning and falls back to instance routes | |
| Q8 | Which org for the repo remote: johnhiemstracreative or jhcreative? | jhcreative, so it can be shown | |
| Q9 | CD.1–CD.3: show the clock (turnaround per step from the event log) in the overview? | Yes: one turnaround column. That's the Cost of Delay story | |
| Q10 | Demo login: one login with a role switcher, or a login per role? | One login plus the switcher; four windows, one presenter | |
| Q11 | The deploy on Monday morning is on your go (OPS-5). What time do you want the dry-run report? | Sunday 8 pm | |

## Answers so far (2026-11-14)

| # | Answer |
|---|---|
| W1 | No over-cap case in the first example. Happy path first, made canon: simple, self-explaining, less narration |
| W2 | Right. The expectation is a Playwright narrative per view: coordinator, then dispatch and onsite, then controller, then the overview for executives and oversight. Breadth over depth: baseline usefulness for each user, onsite updates the source in real time, no service-type options, option trees or time-tracking sub-views |
| W3 | Approved |
| Q1a | Yes: a new OVH box as JHC's apps home (VPS-2), reused for future work the way the curationapp box was; curationapp.com goes on it after Monday (its old box is shut down); johnhiemstra.com can move from Hetzner later |
| Q1b | `apps.johnhiemstra.com`, then `ofs.apps.johnhiemstra.com` |
| Q3 | Yes, Claude drafts intake |
| Q4 | Fictional but recognizable: the mock Target reasonably clear |
| Q5 | Role names only |
| AG Grid | Use AG Grid for grid interfaces, not hand-rolled: the real-world model for commercial clients with large data sets after this project (ADR 2026-11-14) |
| FacilIT | Real, and kept real as a unique wildcard; its line on the flows reads "Client portal manager"; leadership may not know how much of it some people already use |
| AG1 | Community only until future demand |
| N1 | "Bullseye" for the mock Target; the others are right |
| Q6 | John's choice: deploy the app, share the repo, email a summary with the deck attached. Stretch: the Playwright narratives in an in-app help panel, hosted on John's YouTube |
| Q8 | Defaulted: jhcreative |
| Q10 | Defaulted: one login plus the role switcher |
