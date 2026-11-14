# POC-04: commands, the rails, the logins (11:29 to 11:45)

**Goal:** every transition and rail tested, and one login per role (plan §6, Q10).

## Built

- **`ofs/commands.py`:** the only way a job moves. A command is checked in order: it exists; the role may issue it,
  and a tech acts only on their own job; the view saw the latest version (`expected_event_id`); the job is in a state
  the command starts from; the payload is valid; and the rails hold. Then the job and one event are written in one
  transaction. A refusal writes nothing, and says what to do in a sentence.
- **The rails (plan §4):**
  - Hard, no override: no dispatch until a required approval is on record; no close without a sign-off or a reason;
    no approval of an invoice that failed its check.
  - Soft: assigning a tech outside their skill or license takes a reason, recorded on the event.
- **Two-way fields (`update_fields`):** the coordinator and the job's own tech edit the same typed fields. Identity is
  never editable, and the rules are re-evaluated on every edit.
- **`ofs/auth.py`, five logins** (`coord@`, `dispatch@`, `tech@`, `controller@`, `exec@ofs.com`):
  - bcrypt, and an HttpOnly, SameSite=Lax cookie that's Secure by default;
  - the account re-read on every request;
  - a login rate limit and an Origin check on every write;
  - the same answer for a wrong password and an unknown email.
  - Each defence is written in the code beside the threat it answers.
- **`ofs/logins.py`:** generates the passwords straight into a file readable only by its owner, and prints only the
  emails. The file now lives in `~/jhc/secrets/jahnel-poc/` (John's yes).
- **Role-scoped reads (`ofs/api.py`):** a tech sees only their own jobs; exec reads everything and changes nothing.

## Verified

- 58 tests passed.
- **Every person-issued command is refused from every wrong state,** with nothing written.
- **Roles and staleness:** roles are refused by name, and a stale view gets a 409.
- **Overrides:** the hard rails refuse even with an override reason, and the soft one records it.
- **The happy path over HTTP** with real logins, from intake draft to the QuickBooks row: the test checks all nine
  history events and who did each step.

## Found

- **A seed defect:** 33 of 45 jobs sat over their client's cap, against the plan's "a few", so the happy path was the
  exception. Fixed, and pinned by a test: 3 to 12 over, and drafts with no rule.
- **Two empty assertions of my own:** both ended in `or True`, so they couldn't fail. Our conventions forbid tests
  that test nothing, so they were fixed to check the real history.

## Mineable

- **Commands in, events out:** "a view never writes to another view" (plan §4) is now `execute()`. Every change has
  an author, a time, and a reason when one was needed.
