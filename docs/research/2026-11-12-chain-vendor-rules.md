# Chain vendor rules: Target, CVS Health, Walgreens, Wegmans, ALDI (US)

Research date 2026-11-12. Public pages only; no logins. Every claim carries a source number (see Sources).
Tags: **[official]** the chain's own page; **[platform]** the work-order platform's own page or guide;
**[vendor marketing]** a platform case study or testimonial naming the chain; **[job posting]**;
**[single unofficial]** one third-party or unverified source; **[inferred]** our reading, not a stated fact.
Search-engine snippets we could not open and confirm are marked **[snippet, unverified]**.

## Summary: the cross-chain pattern

Three of the five chains (CVS, Walgreens, ALDI) have public evidence pointing to **ServiceChannel** as the
vendor work-order platform, all of it from ServiceChannel's own marketing or job postings; Wegmans and Target
name only an internal CMMS/EAM (Target: IBM Maximo), and no vendor-facing platform was found for either. Where ServiceChannel governs, the rules are the platform's, and they line up exactly
with the client's three loss causes: every work order is dispatched **with an NTE**; work above the NTE needs a
**proposal approved before work or parts**, and "customers retain the right to refuse invoices for unapproved
work" [S1]; **check-in/out by GPS app (quarter-mile geofence) or IVR** is the proof of presence the client's
billing is checked against [S1][S3][S5]; completion may sit in **"Pending Confirmation" for about 5 days** until
the store or facility manager signs off, and photos are expected [S1]; invoices go **only through the
platform, one per work order, within the NTE, with a labour/material/trip breakout, within 10 days, and
never after 90 days** [S1]. CVS says outright it "dispatch[es] everything with an NTE, knowing intentionally
that many times the provider has to come back" for approval [S3]. Approval to work is insurance-first: COI with
the chain as additional insured, W-9, a third-party screen (Walgreens: GRMS) [S8], and ongoing scorecards on
SLA, check-in compliance and first-time fix [S1][S4]. **[inferred]** The dispute losses the client describes are
what this system is built to produce when NTE increases are verbal, check-ins are missed, or confirmation is
skipped: the platform simply has no record that the work was approved.

## Target

1. **Platform.** Target's own postings name **IBM Maximo** as its asset-management system; technicians "create
   and close work orders" there and validate outside specialty contractors' work [S12][S13] **[job posting,
   snippet, unverified: pages render by script]**. No public source names a vendor-facing platform
   (ServiceChannel, Corrigo, Fexa) for Target stores: **not found**. Target Partners Online (POL) is the
   merchandise-supplier portal, invoiced by EDI 810 [S14] **[single unofficial]**; not shown to apply to
   facilities vendors.
2. **Work orders and NTE.** Store Property Management Leads "ensure internal and external work orders are
   completed safely and efficiently; vendors are accountable to do the same for work orders assigned/routed to
   them" [S11] **[official]**. NTE limits and the increase process: **not found**.
3. **Check-in/out, sign-off.** **Not found.** **[inferred]** The Property Management Lead role (vendor
   accountability, "vendor performance meets maintenance" standards) is the likely on-site sign-off [S11].
4. **Invoicing.** For facilities vendors: **not found**.
5. **Approved vendor.** For facilities vendors: **not found**. Merchandise-supplier guides cite general and
   product liability with Target as additional insured, at limits that disagree between sources [S15]
   **[single unofficial; merchandise, not facilities]**.

**Thin.** Target publishes nothing public on facilities-vendor rules; this needs a client contact or a
vendor who already serves Target.

## CVS Health

1. **Platform.** **ServiceChannel.** CVS's Sr. Director of Facility Management describes overseeing "hundreds of
   third party service contractors" through it [S3]; CVS uses ServiceChannel's contractor-initiated work order
   app for snow [S4] **[vendor marketing; S3 dated 2016, S4 undated]**. Mandatory use: **[inferred]** yes, since
   check-in, proposals and invoices are all tracked in the platform [S3][S4].
2. **Work orders and NTE.** "They dispatch everything with an NTE, 'knowing intentionally that many times the
   provider has to come back' to them and seek their approval"; CVS sometimes answers a proposal with "don't
   repair that, replace it" [S3]. CVS reviews "proposal to NTE trending", time to submit proposals, and
   "proposal vs invoice costs"; proposals can be approved in the mobile app [S4] **[vendor marketing]**.
3. **Check-in/out, sign-off.** Check-in/check-out is tracked per provider [S3]; CVS pushes GPS mobile check-in
   over IVR because it gives "the additional confidence that the provider's billing will be accurate" [S4].
   Smartphone photos are used for visibility on repairs [S3] **[vendor marketing]**. Store-manager signature
   rule: **not found**.
4. **Invoicing.** Through ServiceChannel; CVS tracks "invoicing requirements" and contracted rates per vendor
   [S3]. Before its snow app, "invoices came months later" and it was hard to tell whether the work happened
   [S3]. CVS-specific deadline or attachment list: **not found**; the platform defaults in the ServiceChannel
   section below are the best proxy **[inferred]**.
5. **Approved vendor.** Insurance verified in platform: "do providers actually have insurance, are these policies
   up to date and current, and is CVS named as additionally insured" [S3]; license compliance tracked [S3].
   Providers are compared on on-time arrival, first-time completion, hours on site and work-order aging [S4]
   **[vendor marketing]**. Insurance limits: **not found**.

## Walgreens

1. **Platform.** **ServiceChannel**: a ServiceChannel webinar (Accruent Insights 2023) features "success stories
   from Walgreens" onboarding ServiceChannel for its FM program [S9] **[vendor marketing]**. A vendor
   (Encompass Onsite) case study says it integrated with Walgreens' work-order system, described as
   Accruent's [S10] **[snippet, unverified; page now 404]**. **[inferred]** consistent, since ServiceChannel is
   now sold under Accruent [S16]. A Store Care posting names CBRE as delivering store care programs [S17]
   **[snippet, unverified]**.
2. **Work orders and NTE.** Store Care staff handle "work order approval and rejection through vendor
   relations" [S17] **[snippet, unverified]**. NTE amounts and the increase process: **not found**.
3. **Check-in/out, sign-off.** **Not found** for Walgreens specifically.
4. **Invoicing.** Facilities invoicing: **not found**. Walgreens' SupplierNet/VAIS invoice system is for
   merchandise suppliers [S18] **[single unofficial]**; not shown to apply. Walgreens publishes "Pay Application
   Requirements" for construction partners [S7] **[official; construction, not repair]**.
5. **Approved vendor.** The most complete official page of the five [S8] **[official]**: vendors are reviewed by
   Store Care Program Managers or Facility Asset Managers, then register with **Global Risk Management Solutions
   (GRMS)** in the Vendor Screening Program. Required: W-9 signed within 12 months; remittance-address proof;
   COI with Workers' Comp (statutory) and Employers Liability $500K each accident / $500K disease per
   employee / "$550,00" disease policy limit (typo on the page); CGL $2M each occurrence, $2M personal and
   advertising injury, $2M general aggregate, $2M products/completed operations; auto $1M CSL including
   uninsured/underinsured; Walgreens additional insured on all but WC; all policies waive subrogation.
   Inquiries to the vendor-management mailbox named on the page. The page footer reads "Copyright 2016", so the
   limits may be dated.

## Wegmans

1. **Platform.** No vendor-facing platform named: **not found**. Postings ask for experience with an "EAM
   computer system" (Maintenance Operations Center) [S20] and a CMMS (Utilities Maintenance Supervisor) [S21]
   **[job posting; S20 expired, snippet]**. **[inferred]** Wegmans dispatches from an internal centre to
   in-house teams and contractors rather than through a public marketplace.
2. **Work orders and NTE.** The Maintenance Operations Center triages, prioritises and dispatches repair requests
   for stores, facilities and manufacturing [S20] **[job posting, snippet]**. NTE: **not found**.
3. **Check-in/out, sign-off.** **Not found** for repair calls. All contractors take an annual contractor safety
   orientation, sign a sign-off sheet and carry a card on site [S22] **[single unofficial: undated slide deck]**.
4. **Invoicing.** **Not found.**
5. **Approved vendor.** Coordinators manage vendor service work and complete annual contractor performance
   reviews [S21] **[job posting]**. The only public Wegmans COI sheet is for newspaper/book/magazine suppliers
   [S23] **[official, wrong vendor type]**: CGL $1M occurrence / $2M aggregate, umbrella $1M, Wegmans additional
   insured for ongoing and completed operations two years past completion, certificates held c/o PlusOne
   Solutions (Orlando). **[inferred]** Facilities limits are likely at least this, through the same COI tracker.

**Thin.** Wegmans is the least public of the five; it needs a direct contact.

## ALDI (US)

1. **Platform.** **ServiceChannel**: ALDI's Director of Real Estate is quoted on ServiceChannel's site: "Prior to
   ServiceChannel, we were very reactive. We had a false sense of control over costs. Now we can be more
   proactive with data." [S24] **[vendor marketing]**. ALDI SÜD (ALDI US's parent group) runs a "National
   Facility Management (NFM) service provider portal" of ServiceChannel training, including technician
   check-in/out material [S25] **[official, Germany; US applicability inferred]**. US Facilities Managers
   "oversee repair and maintenance expenditures through regularly scheduled site visits and CMMS" for "up to
   150 ALDI locations" [S26] **[job posting]**; one listing reportedly names ServiceChannel [S27] **[snippet,
   unverified]**.
2. **Work orders and NTE.** **Not found** for ALDI specifically.
3. **Check-in/out, sign-off.** ALDI SÜD's portal has a check-in/check-out training section for technicians
   [S25]; its content was not readable publicly. ALDI US rules: **not found**.
4. **Invoicing.** **Not found** for facilities. ALDI prefers EDI for merchandise POs and invoices [S28]
   **[official, merchandise]**.
5. **Approved vendor.** Facilities service providers apply through ALDI's prospective vendor application [S28]
   **[official]**; non-merchandise inquiries go to ALDI Procurement [S28]. Suppliers provide a COI and sign the
   ALDI Master Purchase Agreement [S29] **[official, aimed at merchandise suppliers]**. Facilities limits:
   **not found**.

**Thin** on the process; strong on the platform.

## The ServiceChannel rulebook (applies wherever a chain dispatches through it)

From ServiceChannel's 2026 Trade Partner Guide [S1] **[platform; written for its Managed program, the best
public statement of platform defaults; each client can configure its own]**:

- **Accept**: accept or decline within 30 minutes (15 for emergencies); declines need a reason and are scored.
- **NTE**: every work order carries scope, location, SLA and NTE. If the first-visit job "will exceed the NTE
  amount, call for approval before proceeding." If parts exceed the NTE, "a proposal must be submitted and
  approved before parts are ordered." Proposals within 48 hours (24 emergency), with photos, diagnostics, parts
  with part numbers, labour as hours x approved rate x techs, travel, freight, total. "All proposals must be
  approved by ServiceChannel or the customer prior to the start of work." Quotes held 30 days. "You won't be
  able to check in if the proposal has not been approved. Customers retain the right to refuse invoices for
  unapproved work."
- **Check-in/out**: by the mobile app, IVR "only used as back-up"; the app works only "within a quarter mile of
  the site"; KPI goal 90% of reactive work orders with a matched check-in and check-out; "always check-in and
  check-out with a manager onsite." IVR uses a PIN plus work-order number [S5][S6].
- **Sign-off**: on completion the tech checks out and enters root-cause and resolution codes; the app takes
  before/after photos and notifies the location manager the work is "ready for inspection". Status
  "Completed/Pending Confirmation": the location or facility manager gives feedback, "typically within 5 days";
  "Unsatisfactory" if the manager rejects the work.
- **Invoice**: "Submit all your invoices on the ServiceChannel platform"; one invoice per work order; within 10
  days of Completed/Confirmed; after 90 days uninvoiced the work order becomes "ineligible for billing"; must
  be within the NTE with a breakout of labour, techs, materials, trip charge and freight; attach subcontractor
  invoices; sales tax only when billing the customer.
- **Rejection mechanics** [S2] **[platform help]**: an invoice cannot exceed its NTE; a rejected invoice "cannot
  be edited" and must be resubmitted under a new number; rate mismatches against agreed rates require a
  comment; system errors include a blank work-order number and duplicate invoice numbers.
- **Scorecard**: tiers at 90%+, 70 to 89%, and 69% or below; the bottom tier gets quarterly corrective-action
  calls and, after three quarters without improvement, possible removal. KPIs include emergency SLA, check-in
  compliance, schedule-date compliance, proposal submission time and declines.
- **Onboarding**: accept the Fixxbook invitation, upload COI (certificate holder must match exactly) and all
  custom requirements before receiving work orders.

## Sources

- S1 ServiceChannel, Trade Partner Guide 2026: https://servicechannel.com/wp-content/uploads/2025/10/Trade-Partner-Guidelines-2026.pdf
- S2 ServiceChannel University, invoice statuses and rejection: https://servicechannel.atlassian.net/wiki/x/UgHIJ ; https://servicechannel.atlassian.net/wiki/spaces/SCUCP/pages/616923364/Creating+an+Invoice+in+Provider+Automation ; https://servicechannel.atlassian.net/wiki/download/attachments/617054507/I11_ErrorCodes%20(1).pdf?api=v2 (snippets via search)
- S3 ServiceChannel blog, 3 Keys for CVS Health Facilities (2016): https://servicechannel.com/blog/3-keys-cvs-facilities-get-transparent-video/
- S4 ServiceChannel blog, Webinar with CVS Health: https://servicechannel.com/blog/webinar-with-cvs-health-how-to-elevate-facilities-management-within-your-organization/
- S5 ServiceChannel, IVR check-in (SCUniversity): https://servicechannel.atlassian.net/wiki/spaces/SCUCP/pages/579764555
- S6 ServiceChannel, Provider Support contact: https://servicechannel.com/tools/provider-support-contact-us/
- S7 Walgreens Facilities, Construction Partner Requirements: http://facilities.walgreens.com/partners/construction-partner-requirements.html
- S8 Walgreens Facilities, Become a Facilities Maintenance Partner: http://facilities.walgreens.com/partners/become-a-maintenance-partner.html
- S9 ServiceChannel webinar, Leaders in Brand Preservation (Walgreens): https://servicechannel.com/webinars/leaders-in-brand-preservation-leveraging-servicechannel-to-optimize-facilities-and-assets/
- S10 Encompass Onsite, Walgreens case study (404 at check): https://encompassonsite.com/case-studies/how-encompass-simplified-and-scaled-facility-management-for-walgreens
- S11 Target careers, Property Management Lead: https://corporate.target.com/careers/career-areas/stores/hourly/property-management
- S12 Target, Sr Facility Engineer, Suffolk VA (404 at check): https://corporate.target.com/jobs/w11/44/sr-facility-engineer-upstream-distribution-center-suffolk,-va
- S13 Target, Maintenance Technician 3, Stuarts Draft VA: https://corporate.target.com/jobs/w10/11/maintenance-technician-3-regional-distribution-center-stuarts-draft,-va
- S14 iNymbus, Target Partners Online guide: https://blog.inymbus.com/target-partners-online-a-complete-guide-for-suppliers
- S15 RetailerHub, How to sell to Target: https://www.retailerhub.ai/guides/how-to-sell-to-target ; Warpspeed: https://gowarpspeed.com/retailers/target
- S16 Accruent, Transform Your Operations with ServiceChannel: https://info.accruent.com/rs/167-BOY-362/images/Transform-Your-Operations-with-ServiceChannel.pdf
- S17 Walgreens, Analyst Store Care Data Management (404 at check): https://jobs.walgreens.com/en/job/deerfield/analyst-store-care-data-management/1242/73602835024
- S18 Logicbroker, Walgreens invoice submission: https://support.logicbroker.com/kb/walgreens/360049003472-how-do-i-submit-my-invoice-and-check-payment-status
- S20 Wegmans, Maintenance Operations Center Specialist (expired): https://jobs.jobg8.com/job/maintenance-operations-center-specialist-in-rochester-new-york-4658-2762730751FF
- S21 Wegmans, Utilities Facilities Maintenance Coordinator / Supervisor: https://www.themuse.com/jobs/wegmansfoodmarkets/utilities-facilities-maintenance-coordinator ; https://www.themuse.com/jobs/wegmansfoodmarkets/utilities-facilities-maintenance-supervisor
- S22 SlideServe, Wegmans Ammonia Safety Management for Contractors: https://www.slideserve.com/daiello/wegmans-process-safety-management-ammonia-awareness-affecting-contractors-powerpoint-ppt-presentation
- S23 Wegmans, COI requirements (newspapers, books, magazines): https://images.wegmans.com/is/content/wegmanscsprod/Newspapers-Books-Magazines-certificate-of-insurance-requirementspdf-1
- S24 ServiceChannel, Platform Data Insights (ALDI quote): https://servicechannel.com/platform-data-insights/
- S25 ALDI SÜD, service provider portal (ServiceChannel): https://www.aldi-sued.de/supplieronboarding/Dienstleister_Handling_Englisch/servicechannel
- S26 ALDI, Facilities Manager, Baltimore MD (mirror): https://blackcareernetwork.com/job/facilities-manager-13
- S27 ALDI, Facilities Manager (careers.aldi.us): https://careers.aldi.us/job/philadelphia/facilities-manager/61/98896190784
- S28 ALDI US, Become a Supplier: https://corporate.aldi.us/suppliers/become-a-supplier
- S29 ALDI US, Supplier FAQs: https://corporate.aldi.us/suppliers/faqs
