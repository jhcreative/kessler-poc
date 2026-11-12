# Facil-IT deep read: what a service provider gets, and what OneFamilyServices may be leaving unused (2026-11-12)

Public pages only, read 2026-11-12. No logins, no demo forms. Nothing here is confirmed by the client or the vendor.
Follows the first read in `2026-11-12-vendors.md`. Tags: **[vendor]** = the vendor says it on its own page;
**[3rd party]** = a directory or other site; **[single]** = one source only; **[inferred]** = our reading, not a
claim anyone makes. Source keys [F1]..[F12] are listed at the end.

**Note on the domain.** `getfacilit.com` and `www.getfacilit.com` do not resolve; only the `info.` landing page
answers [F1]. The product's own site is **facilit.fm** [F2–F5], and TMA Systems hosts a mirror of the same pages
[F6–F9]. The **"Facil-IT" iPhone app on the App Store is someone else's** (Exaforte B.V., cleaning-company
scheduling) [F12], and "Facil-ITy" on the App Store is from Intelligent Data Systems [F12]. No App Store or Google
Play listing for the TMA/Facil-IT field app was found.

## 1. Summary: what looks underutilized

The client described Facil-IT as "a connection" it pays for. The vendor describes a **full provider-side
operating system**: "The operating system for commercial service providers" [F2], work order to invoice "in one
flow" [F1]. Set against the client's picture, the gap looks like this:

1. **Field app with check-in/out, photos, signatures, offline** [F3, F6] **[vendor]**, plus geofenced mobile IVR and
   phone IVR check-in/out that sync to the client's CMMS [F3] **[vendor]**. Techs texting photos from personal
   phones suggests this is unused, **[inferred]**, and it attacks "missing sign-off" directly.
2. **Proposals, bidding and client approval in a portal** [F3, F6] **[vendor]**, with configurable "statuses,
   approvals, notifications, and completion requirements" [F3]. The vendor never says "NTE" (**not found**), but a
   completion requirement or an approval gate is where an NTE guard would live **[inferred]**. The chains' own
   portals already refuse an invoice over NTE (ServiceChannel: "an invoice cannot be submitted for more than its
   not-to-exceed (NTE) amount") [F11] **[3rd party, snippet]**, so over-cap work without an approved increase is
   money the portal will never pay.
3. **Built-in AR/AP and native QuickBooks Online** ("export invoices, bills, and transactions; import client
   payments; multi-division support") [F4] **[vendor]**. One person hand-keying QuickBooks suggests this is off or
   not in their edition ("integrated accounting available in select editions" [F1]).
4. **Rule-based and proximity dispatch, vendor portal, scorecards, compliance reminders** for W-2 techs and 1099
   subs "side by side" [F1, F3] **[vendor]**. One dispatcher on his phone suggests none of it is in use **[inferred]**.
5. **Connectors well beyond the small clients**: ServiceChannel, Corrigo, Fexa, FM Pilot, OfficeTrax, EcoTrak and
   **IBM Maximo** [F4] **[vendor]**. Our chain research found Target names Maximo as its own system
   (`2026-11-12-chain-vendor-rules.md`) **[3rd party; link to Target inferred]**. Whether Target's vendor feed is
   reachable through that connector is unknown.
6. **An open REST API and a SQL replica for BI** [F4, F3] **[vendor]**: the data could leave Facil-IT without
   re-keying, which matters for any POC we build beside it.

**Read [inferred]:** the client may be paying for the connector tier of a product that could be its system of
record for every client, field app and billing included. Or its edition excludes these. Either answer reshapes
the POC; ask before building any of it.

## 2. Capability table

| # | Capability | What the vendor says | Source | Basis | Client problem it could address |
|---|---|---|---|---|---|
| 1 | Intake from client systems | ServiceChannel: "Full two-way sync via XML or API, with TPT subcontractor support and IVR check-in/check-out". Corrigo: "Automated work order exchange with configurable line-item sync". Fexa: "Pre-configured bi-directional API connection". Also FM Pilot ("Full two-way API"), OfficeTrax ("Work order intake and status updates"), EcoTrak, Maximo ("vendor ID mapping"); Nuvolo "Coming soon" | [F4], [F7] | vendor | Hand-keying from portals. Automatic is implied by "sync" and "automated", not stated per field. Target portal and Starbucks email: **not found** as connectors |
| 2 | Intake from email / attachments | Not found. Client portal lets clients "submit requests" with photos and documents | [F3] | vendor (portal); email **not found** | Starbucks store emails, client emails: a portal could replace some email; email parsing not offered publicly |
| 3 | NTE / not-to-exceed | **Not found** on any Facil-IT page | [F1–F9] | — | Over-NTE disputes. Closest: configurable approvals and completion requirements [F3] **[inferred]** |
| 4 | Proposals, quotes, approval | "Bidding & Project Management: proposals, competitive bidding, project rollups, and profitability"; clients "review proposals and invoices alongside related work orders" | [F3], [F6] | vendor | Work over NTE without approval: a proposal approved in the portal is the written record |
| 5 | Field mobile app | "live asset data, tag scanning, time, notes, photos, signatures, and offline use"; techs "check in/out, log time" | [F3], [F6] | vendor; app store listing **not found** | Photos texted from personal phones; missing sign-off |
| 6 | IVR check-in/out | Telephony IVR "time-stamped and synced to client CMMS when integrated"; "Geofenced Mobile IVR" in the app | [F3] | vendor | Proof of arrival and departure the chain's portal accepts; "voice-enabled service verification" also in the press release [F10] |
| 7 | Dispatch / scheduling | "Rule-Based Vendor Dispatch" by client, location, trade, category; "Proximity-Based Dispatch Mapping"; smart dispatch by "trade, location, availability, SLA requirements"; PM work orders generated automatically; storm-triggered snow dispatch | [F3], [F7], [F5] | vendor | One dispatcher on a phone. Samsara integration: **not found** [F4] |
| 8 | Subcontractor management | Vendor portal "accept work, submit bids, upload documentation, invoice"; scorecards; insurance and license expiry reminders; AP "gated by paperwork compliance"; W-2 and 1099 "side by side" | [F3], [F1] | vendor | Subs' paperwork and photos; paying a sub before sign-off |
| 9 | Invoicing to client portals | Built-in AR "batch client invoicing"; ServiceChannel and Fexa connections are "two-way" | [F3], [F4] | vendor (AR); **push of invoices into ServiceChannel/Corrigo/Fexa: not stated** | Rejected invoices. Ask whether the two-way sync carries invoices **[inferred]** |
| 10 | Accounting integration | QuickBooks Online: "Export invoices, bills, and transactions; import client payments; multi-division support"; Sage Intacct, NetSuite, Acumatica, Dynamics; GL export for others | [F4], [F3] | vendor | Billing by hand in QuickBooks. "Integrated accounting available in select editions" [F1]. QuickBooks Desktop: **not found** |
| 11 | Job costing | "Live Job Costing & Profitability: committed and actual costs, revenue, and margins per work order" | [F3] | vendor | Seeing a job head over its cap before the invoice |
| 12 | Contracts / SLA | SLA Monitoring "response and completion targets across client accounts"; "contracts" named on the landing page, no feature described | [F1], [F3] | vendor (SLA); contract terms/rates **not found** | Vague contracts: SLA targets yes; rate cards, NTE per client, scope terms not described |
| 13 | Rules engine / alerts | "custom conditions and actions (email, SMS, status changes, escalation)"; Twilio SMS | [F3], [F4] | vendor | An alert before a job exceeds NTE **[inferred, not claimed]** |
| 14 | Reporting / dashboards | Configurable KPI dashboards; "dozens of built-in reports or request custom reporting"; client-ready reports; audit trails | [F3], [F6], [F1] | vendor | Measuring the $80K–$200K dispute loss by client and cause |
| 15 | API / data export | "RESTful API ... JWT authentication and scope-based permissions"; "Open BI Data Feed ... auto-refreshed SQL replica"; Power BI connector | [F4], [F3] | vendor | A POC that reads Facil-IT data without re-keying |
| 16 | Client portal | Clients submit requests, track status, review proposals and invoices, attach photos | [F3] | vendor | Smaller clients emailing: give them the portal |
| 17 | Services | Implementation, role-based training, named consultant, "Admin as a service"; custom integrations "Available for Enterprise customers" | [F8] | vendor | A Target or Starbucks connector may be an Enterprise build |
| 18 | Pricing / editions | No prices or edition names; "customized cost estimate" by form; quote-based | [F9], [F12 SoftwareFinder] | vendor + 3rd party | What their current tier excludes is the first unknown |
| 19 | Reviews | Facil-IT: 0 reviews found (SoftwareFinder "No reviews yet!"); G2/Capterra entries are for WebTMA, not Facil-IT | [F12] | 3rd party | No outside evidence on how well any of the above works |
| 20 | System of record for all clients? | Positioned for "multiple clients, locations, portals, and service lines" in one place; client portal for clients without a CMMS | [F2], [F3] | vendor; fit for OFS **[inferred]** | Possible for portal-less clients (portal) and connected chains; Target and Starbucks intake paths **not found** |

## 3. Candidate discovery questions for the COO

1. **Edition and modules (rows 10, 17, 18).** Which Facil-IT edition do you pay for, and is it the connector only,
   or does it include the field app, AR/AP and the QuickBooks Online link? Who at Facil-IT is your named consultant?
2. **Field app (rows 5, 6).** Has anyone at OneFamilyServices been offered the Facil-IT tech app or IVR check-in? If
   so, what stopped the techs from using it instead of texting photos?
3. **Approvals before work (rows 3, 4, 13).** When a tech finds the job will run over the NTE, what happens today, step
   by step? Has Facil-IT shown you its proposal approval or an approval-required status for over-cap work?
4. **Invoices into portals (row 9).** For ServiceChannel, Corrigo or Fexa clients, does the invoice go back through
   Facil-IT, or does someone re-key it into the client's portal? Which of your rejected invoices came from those clients?
5. **Target and Starbucks (rows 1, 2, 17).** Has Facil-IT ever quoted connecting Target's work order feed (Target
   runs Maximo, which Facil-IT lists) or a Starbucks intake? What did they say it would take?
6. **One system or two (row 20).** Which work lives in Facil-IT today and which in FieldOPS/FieldDesk? If Facil-IT could
   hold every client's jobs, what would make you keep FieldOPS?
7. **Subcontractors (row 8).** Do your subs ever touch Facil-IT, through its vendor portal, or only by text and phone?
8. **Data out (rows 14, 15).** Can you export a year of jobs with NTE, final invoice and dispute outcome from either
   system? If not, who would ask Facil-IT for API or BI-feed access?

## 4. Sources

- F1 Facil-IT landing page, Commercial Service Provider Software: https://info.getfacilit.com/commercial-service-provider-software
- F2 Facil-IT home: https://www.facilit.fm/
- F3 Facil-IT, Our Features: https://www.facilit.fm/our-features/
- F4 Facil-IT, Integrations: https://www.facilit.fm/integrations/
- F5 Facil-IT, About Us: https://www.facilit.fm/about-us/
- F6 TMA Systems, Facil-IT Features: https://tmasystems.com/products/facil-it/features
- F7 TMA Systems, Facil-IT overview: https://www.tmasystems.com/products/facil-it
- F8 TMA Systems, Facil-IT Services: https://tmasystems.com/products/facil-it/services
- F9 TMA Systems, Plans & Pricing: https://tmasystems.com/pricing
- F10 TMA Systems press release, TMA Systems Acquires Facil-IT (2025-09-09): https://www.tmasystems.com/press/tma-systems-acquires-facil-it
- F11 ServiceChannel help, Creating an Invoice in Provider Automation (NTE rule read from search snippet; page body
  did not render): https://servicechannel.atlassian.net/wiki/spaces/SCUCP/pages/616923364/Creating+an+Invoice+in+Provider+Automation ;
  ServiceChannel NTE ebook: https://servicechannel.com/wp-content/uploads/2025/10/servicechannel_NTE-ebook_100125.pdf
- F12 Third-party listings: SoftwareFinder https://softwarefinder.com/cmms/facil-it ; App Store "Facil-IT"
  (Exaforte, unrelated) https://apps.apple.com/be/app/facil-it/id6450011491 ; WebTMA on Capterra (TMA's other
  product) https://www.capterra.com/p/15155/TMA/
- Sibling notes: `2026-11-12-vendors.md` (first read), `2026-11-12-chain-vendor-rules.md` (Target on Maximo)

**Not reachable or not found:** getfacilit.com root (DNS fails); Software Advice, GoodFirms and G2 Facil-IT pages
(HTTP 403); a Facil-IT YouTube channel; Fexa or ServiceChannel partner pages naming Facil-IT; any Facil-IT help
center or knowledge base; any NTE feature; any Samsara or telematics link.
