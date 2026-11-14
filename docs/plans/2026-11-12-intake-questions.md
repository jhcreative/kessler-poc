# Intake: Socratic rounds (Angela, 2026-11-12)

John answers each batch from his notes and his first reflections. Answers fold into
`docs/meetings/2026-11-12-round-4-discovery.md`.

## The map

1. The nine steps and where it leaks
2. People, systems, data
3. What must never go wrong, and the expansion
4. What you committed to, and the step-5 brief
5. Your call: the number, the workstream, the POC

## Batch 1: the nine steps and where it leaks

| # | Question | Answer |
|---|---|---|
| 1 | Walk the nine steps, request to payment, one line each: what happens, who does it, in what system. | 1 intake, 2 coordination, 3 estimation, 4 dispatch, 5 onsite, 6 close, 7 billing, 8 invoicing, 9 collection/aging. One step at a time. |
| 2 | Where did Dana say the waste and leakage show up: which steps, and in what form (hours, money, lost work, work done but not billed, late payment)? | |
| 3 | What numbers came up: request volume, average ticket, days from request to payment, leakage in dollars or percent? Say which she gave and which you estimated. | |
| 4 | How do the chains send work in: their own facilities platform or portal, email, phone? Does each chain do it differently? | |
| 5 | Your first reflection: if you had to bet now, which step leaks the most, and what did she say that makes you think so? | |

Batch 1 questions 2–5 fold into the step-by-step rounds below.

## Step 1: Intake

| # | Question | Answer |
|---|---|---|
| 1.1 | What arrives, and how? Channels per chain (their portal, email, phone), and roughly how many requests a day or week. | Target portal login; Starbucks store emails; others email + attachments; hand entry into FieldDesk; FacilIT for some. Volume open. |
| 1.2 | Who does intake at HQ, how many people, and what system do they enter it into? | |
| 1.3 | What do the chains hold OneFamilyServices to at intake: response times, priority levels, a not-to-exceed amount, penalties? | |
| 1.4 | What goes wrong here, in Dana's words: lost or duplicate requests, missing details (site, equipment, urgency), wrong priority? | |
| 1.5 | Your reflection: what does intake leak, and what number would show it? | |

### Step 1, follow-ups

| # | Question | Answer |
|---|---|---|
| 1.6 | Volume and people: how many requests a week, how many intake staff, and does anyone own each channel (who checks the Target portal, and how often)? | |
| 1.7 | "Accurately": how does anyone know an entry is right before the coordinator gets it? What happens when it's wrong? | |
| 1.8 | The chains' rules at intake: response times, priority levels, a cap on cost without approval, penalties? Did Dana name any? | |
| 1.9 | FacilIT: what do you know (which clients, what flows through it, what OF pays)? And is it a name from the role play we should treat as a black box with an assumed interface, rather than research? (Same question for FieldDesk.) | |
| 1.10 | Your reflection: what does intake leak, and what number would show it? | |

## Steps 2–5 (answered 2026-11-12; notes in the meeting record)

### Follow-ups

| # | Question | Answer |
|---|---|---|
| 2.1 | Are the three intake people also the coordinators? How many coordinators, techs and trucks in all, and how many open jobs does one coordinator carry? | |
| 3.1 | Work done without approval: does the client pay anyway, dispute it, or does OF eat it? Did Dana put a figure on it? | $80K–$200K a year in disputed invoices for work not approved first. |
| 3.2 | Price caps and approval patterns: where do they live today (contract PDFs, someone's head), and how many rule sets: one per client, or per client by issue type? | |
| 4.1 | Tony: what does he decide, with what information, and what happened the last time he was out? | |
| 5.1 | Replace the empty notes field with five to eight fields: what are they? | Answered: see `2026-11-12-job-record-draft.md`. |

### On the $80K–$200K

| # | Question | Answer |
|---|---|---|
| 3.3 | Is that the disputed amount or the lost amount? How much is eventually won back, and what does winning it back cost in staff time? | Lost: written off in accounting. |
| 3.4 | Did Dana give it, or is it your estimate from what she said? Why a range that wide? | Dana's. |
| 3.5 | The average job size, roughly, so we know what share of revenue that is. | $2,000–$50,000 (Dana). |

## Working hypothesis for the POC (Angela, 2026-11-12, not yet approved)

Contract rules (caps and approval patterns per client, per issue type) reach the coordinator and the tech before work,
and the system gates any estimate over a cap; each estimate is scored against the history of like jobs.

| # | Question | Answer |
|---|---|---|
| H.1 | Volume check: 80,000 requests a year at $2,000+ each is $160M+ in revenue. Does that match Dana's company, or are most "requests" smaller than a job (calls, follow-ups, small fixes)? | |
| H.2 | If the leak is $80K–$200K on that revenue, is the bigger prize elsewhere (estimate accuracy, days to payment in steps 7–9)? Hold until we've walked 6–9? | |
| H.3 | "Like jobs": what makes two jobs alike? Client, issue type, equipment, region, season? | |

| H.4 | With Target on its own portal, smaller clients on FacilIT and the rest on email into FieldDesk: where should the contract rules and the job record live? In one of those, or in a layer above all of them? | FacilIT stays (a necessary dependency). FieldDesk holds the truth but hides it: no request state, no turnaround data. Points to a layer above. |

### Visibility

| # | Question | Answer |
|---|---|---|
| V.1 | Who most needs to see a request's state, and what question are they asking? (Dana: "are we on time?"; a coordinator: "what's stuck?"; Tony: "who's free?"; a client: "where's my repair?") | |
| V.2 | Can data get out of FieldDesk at all: an export, reports, an API? Did Dana say? | |
| V.3 | Turnaround: from which step to which step does Dana care most? Request to onsite, onsite to invoice, invoice to paid? | |

## Steps 6–9 (answered 2026-11-12; notes in the meeting record)

| # | Question | Answer |
|---|---|---|
| 6.1 | How does Marcee learn a job closed, and how many days pass from close to invoice? | Marcee pulls completed work reports from FieldDesk; timing varies with volume. |
| 7.1 | When she matches a job to its contract, PO and signature, what's missing most often, and how does she chase it? | The client's local rep signs off on the work in the field. |
| 8.1 | How many invoice formats or portals does she deliver to? | About a dozen strict formats. Research Target, CVS, Walgreens, Wegmans, ALDI. |
| 9.1 | How much sits past 60 or 90 days? Did Dana give days to payment? | Not the concern; disputes are. |
| 9.2 | Where do the $80K–$200K disputes surface: when the client rejects the invoice, or later? Who finds out first? | After all is said and done. OF invoices anyway when the signature is missing or the contract is vague: the only way to get paid. |

## Next discovery round: FacilIT (from `docs/research/2026-11-12-facilit-deep.md`, for Dana)

| # | Question | Answer |
|---|---|---|
| FI.1 | Which FacilIT edition do you pay for: the connector only, or with the field app, AR/AP and the QuickBooks Online link? | |
| FI.2 | Has anyone offered your techs the FacilIT app or phone check-in? What stopped them? | |
| FI.3 | When a job will run over the cap, what happens today, step by step? Has FacilIT shown you its proposal approval? | |
| FI.4 | For clients on ServiceChannel, Corrigo or Fexa, does the invoice go back through FacilIT, or is it re-keyed? | |
| FI.5 | Has FacilIT ever quoted connecting Target (Maximo, which FacilIT lists) or Starbucks? | |
| FI.6 | Which work lives in FacilIT and which in FieldDesk? If FacilIT held every client's jobs, what would keep FieldDesk? | |
| FI.7 | Can either system export a year of jobs with the cap, the final invoice and the dispute outcome? | |

**When (FR.2, John, 2026-11-12):** wait. FI.1–FI.7 go to Dana in a later round, not in the follow-up email.

## Architecture (FR, John, 2026-11-12)

| # | Question | Answer |
|---|---|---|
| FR.1 | (a) our own layer over every system, or (b) FacilIT as the core? | A harness that includes FacilIT, not a core. Recorded in `docs/adr/2026-11-12-a-harness-with-adapters-not-a-core.md`. |
| FR.2 | FI.1–FI.7 in the email now, or a later round? | Wait. |
| FR.3 | One field app for every job (ours), or FacilIT's app for FacilIT jobs? | One app. |
| N.1 | Next: the POC plan, flow 1's graphic, or flow 2 as data? | Draw the flows, in a readable PDF, with the ADR basics first. |

**FacilIT, John 2026-11-14:** real, and kept real going forward as a unique wildcard ("Client portal manager"). We may
want to use more of its capabilities, or we may find some people already do and leadership isn't in the loop on those
details. FI.1–FI.7 should ask who uses it and how, not only what the edition includes.
