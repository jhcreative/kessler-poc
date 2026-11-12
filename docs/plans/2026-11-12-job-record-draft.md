# The job record: draft 1 (John, written up by Pete, 2026-11-12)

Not approved. John's answer to 5.1, in his words first, then the draft.

> "where is this notes field? whos reading or updating it? they should be same typed fields across all interfaces and
> users reflecting one current truth for client request. … best practices would already provide structured data for
> client, location, and identifying data for request and contact info at location - it came in from request and
> matches a contractual obligation, no human changes it really - THEN structured fields instead of single 'notes' that
> vary by request and should be passed two ways as required"

## Principle

One job record, the same typed fields in every interface and for every user: the single current truth for a client
request. Fields pass both ways (office and field) as each step requires.

## Part A: identity (set at intake, matches the contract, nobody edits it)

| Field | Source |
|---|---|
| Client | The request; must match a contract |
| Location (site) | The request |
| Client's request identifiers (work order number, PO) | The request |
| Site contact | The request |

## Part B: the working fields (replace the notes field; two-way)

| Field | Values | Note |
|---|---|---|
| Issue type | A list per contract | Tied to pricing controls (the cap) |
| Parts required | None · on truck · special order | |
| Part numbers | List | Ties special orders to the job (step 5 gap) |
| Estimated hours, from history | Number | From like jobs (H.3 defines "like") |
| Actual hours, this request | Number | |
| Extenuating circumstances | Best guess (D.3): access denied · after hours · return visit · scope changed · safety hold · parts delay · other; plus one short line | Assumption for the exercise; research later |

## Part C: approval (John, D.1)

| Field | Values | Note |
|---|---|---|
| Requires approval | Yes / no, set by rules | Rules per client: the cap for the issue type, or any other logic we find (e.g. "HVAC costs require additional review") |
| Rule that fired | Text from the rule | Says why, so nobody argues with a bare flag |
| Approval | Signature, who, when, client reference | Captured in a signature screen in an app. Nothing exists today. |

## Part D: state (John, D.4: yes)

| Field | Values |
|---|---|
| Current step | 1 intake … 9 collection |
| Owner (coordinator) · assigned tech | People |
| Step history | A timestamp for every step change (gives turnaround and V.1) |

## Assumed for the exercise (D.2 unanswered)

Sign-off: the client rep's signature, before and after photos, check-in and check-out times, on the job record.

## Open (Pete's questions, below)

| # | Question | Answer |
|---|---|---|
| D.1 | Approval: which fields prove it? The cap for this issue type, the estimate amount, approved by whom, when, and the client's reference (portal or email). | A 'requires approval' flag set by per-client rules (cap or other logic, e.g. HVAC review); approval by signature in an app; nothing exists today. |
| D.2 | Sign-off: the client rep's signature, before and after photos, check-in and check-out times. Fields on the job, or attachments? | |
| D.3 | "Extenuating": free text is the notes field again. What are the usual cases (access denied, after hours, return visit, scope changed, safety)? A list plus one short line? | Right thinking; needs research; use a best guess for the exercise. |
| D.4 | State: the job's current step (1–9), its owner, the assigned tech, and a timestamp for every step change. That last one is all V.1 and V.3 need. In? | Yes. |
| D.5 | Who writes and who reads each field? Draft: intake writes A; the coordinator writes issue type; the tech writes parts, hours, photos, sign-off; the system writes the history estimate and the cap check; Marcee reads everything. | Close enough for now. |
