"""The synthetic world (plan §7): deterministic from a seed, so every demo starts the same.

Clients and contracts, 60 sites across seven states, people by role name, ten techs and their trucks, 45 jobs spread
over every state with a history in `job_events`, their invoices, and about 150 historical QuickBooks (simulated)
invoices for the aging summary.

Every job's history is a walk through `states.TRANSITIONS`, checked step by step, so the seed never holds a history
the backend would refuse. Nothing here is real: the clients are fictional but recognizable, the people are role
names, and the coordinates are approximate city centres.

Run: `python -m ofs.seed [--seed N]`. It clears every table first; there is no data here worth keeping.
"""

from __future__ import annotations

import argparse
import asyncio
import random
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from .commands import invoice_check
from .models import (
    Client,
    Contract,
    FleetPosition,
    Invoice,
    Job,
    JobEvent,
    Person,
    QbLedger,
    Site,
    Tech,
)
from .rules import evaluate
from .states import TRANSITIONS, ActorKind, Role, State, allowed

DEFAULT_SEED = 1114

CITIES: dict[str, list[tuple[str, float, float]]] = {
    "PA": [
        ("Allentown", 40.60, -75.47),
        ("Harrisburg", 40.27, -76.88),
        ("Pittsburgh", 40.44, -79.99),
        ("Lancaster", 40.04, -76.31),
    ],
    "OH": [
        ("Columbus", 39.96, -83.00),
        ("Cleveland", 41.50, -81.69),
        ("Youngstown", 41.10, -80.65),
    ],
    "NY": [("Buffalo", 42.89, -78.88), ("Rochester", 43.16, -77.61), ("Binghamton", 42.10, -75.92)],
    "NJ": [("Trenton", 40.22, -74.76), ("Cherry Hill", 39.93, -75.03), ("Newark", 40.74, -74.17)],
    "DE": [("Wilmington", 39.74, -75.55), ("Dover", 39.16, -75.52)],
    "WV": [("Morgantown", 39.63, -79.96), ("Wheeling", 40.06, -80.72)],
    "MD": [
        ("Baltimore", 39.29, -76.61),
        ("Frederick", 39.41, -77.41),
        ("Hagerstown", 39.64, -77.72),
    ],
}
STREETS = (
    "Market St",
    "Main St",
    "Route 22",
    "Union Blvd",
    "Hamilton St",
    "Center Ave",
    "Commerce Dr",
    "Liberty Pike",
    "Ridge Rd",
    "Plaza Way",
)
ISSUE_TYPES = (
    "hvac",
    "refrigeration",
    "electrical",
    "plumbing",
    "doors_locks",
    "lighting",
    "roofing",
    "general",
)
ISSUE_WORDS = {
    "hvac": "rooftop unit not cooling",
    "refrigeration": "walk-in cooler above temperature",
    "electrical": "breaker tripping on the sales floor",
    "plumbing": "restroom leak under the sink",
    "doors_locks": "front entrance door will not lock",
    "lighting": "parking lot lights out",
    "roofing": "roof leak over the stockroom",
    "general": "damaged shelving in the back room",
}


@dataclass(frozen=True)
class ClientSpec:
    name: str
    channel: str
    invoice_format: str
    sites: int
    cap_cents: int
    review: str | None  # an issue type that always needs review
    net_days: int
    wo_prefix: str


CLIENTS = (
    ClientSpec("Bullseye", "portal", "bullseye-portal", 16, 2_500_000, None, 45, "BE-WO-"),
    ClientSpec("Starbrew Coffee", "email", "starbrew-email-pdf", 10, 1_000_000, None, 30, "SB-"),
    ClientSpec("Wellgreens Pharmacy", "email", "wellgreens-csv", 9, 1_500_000, "hvac", 60, "WG-"),
    ClientSpec("CVR Pharmacy", "portal", "cvr-portal", 9, 2_000_000, None, 45, "CVR-"),
    ClientSpec("Wegford Markets", "email", "wegford-edi", 7, 1_200_000, "refrigeration", 30, "WF-"),
    ClientSpec("Aldo Foods", "email", "aldo-pdf", 5, 800_000, None, 30, "AF-"),
    ClientSpec("Keystone Dental Group", "facilit", "facilit-standard", 2, 500_000, None, 30, "KD-"),
    ClientSpec("Lehigh Valley Fitness", "facilit", "facilit-standard", 2, 500_000, None, 30, "LVF-"),
)

# 45 jobs over every state (plan §7: the overview is full on first load).
JOBS_BY_STATE: dict[State, int] = {
    State.INTAKE_DRAFT: 5,
    State.QUALIFIED: 4,
    State.NEEDS_CLIENT_APPROVAL: 3,
    State.READY_FOR_DISPATCH: 5,
    State.ASSIGNED: 5,
    State.ONSITE: 5,
    State.NEEDS_REVIEW: 3,
    State.CLOSED: 2,
    State.BILLING_REVIEW: 5,
    State.INVOICED: 5,
    State.PAID: 3,
}

# Hours each step takes (low, high). Approval and billing review are the slow ones (Cost of Delay).
STEP_HOURS: dict[str, tuple[float, float]] = {
    "draft_intake": (0.0, 0.0),
    "qualify": (0.5, 6),
    "request_client_approval": (0.2, 2),
    "record_client_approval": (4, 48),
    "approve_for_dispatch": (0.2, 4),
    "assign_tech": (0.5, 8),
    "arrive": (2, 30),
    "set_needs_review": (0.5, 4),
    "close_job": (1, 8),
    "draft_invoice": (0.01, 0.1),
    "send_back_invoice": (4, 48),
    "approve_invoice": (4, 96),
    "record_payment": (24 * 20, 24 * 50),
}

# Where the ten techs are based: where the sites cluster, so a recommendation is a drive, not a road trip.
HOMES: tuple[tuple[str, str], ...] = (
    ("PA", "Allentown"),
    ("PA", "Pittsburgh"),
    ("PA", "Harrisburg"),
    ("OH", "Columbus"),
    ("OH", "Cleveland"),
    ("NY", "Rochester"),
    ("NY", "Binghamton"),
    ("NJ", "Newark"),
    ("MD", "Baltimore"),
    ("WV", "Morgantown"),
)
# Licensed in the home state and its neighbours among the seven (a regional firm's techs cross state lines).
NEIGHBOURS: dict[str, list[str]] = {
    "PA": ["OH", "NY", "NJ", "DE", "MD", "WV"],
    "OH": ["PA", "WV"],
    "NY": ["PA", "NJ"],
    "NJ": ["NY", "PA", "DE"],
    "DE": ["PA", "NJ", "MD"],
    "WV": ["OH", "PA", "MD"],
    "MD": ["PA", "DE", "WV"],
}

DEMO_LOGINS = {
    "Coordinator 1": "coord@ofs.com",
    "Dispatcher": "dispatch@ofs.com",
    "Tech 1": "tech@ofs.com",
    "Controller": "controller@ofs.com",
    "Executive": "exec@ofs.com",
}

AGING_BUCKETS = (
    (-30, -1),
    (1, 30),
    (31, 60),
    (61, 90),
    (91, 150),
)  # days past due; negative = not yet due


def path_to(target: State, requires_approval: bool) -> list[str]:
    """The commands that bring a new job to `target`, happy path first (plan §11)."""
    base = ["draft_intake", "qualify"]
    if target is State.INTAKE_DRAFT:
        return ["draft_intake"]
    if target is State.QUALIFIED:
        return base
    if target is State.NEEDS_CLIENT_APPROVAL:
        return [*base, "request_client_approval"]
    if requires_approval:
        base += ["request_client_approval", "record_client_approval"]
    field = ["approve_for_dispatch", "assign_tech", "arrive"]
    tail = {
        State.READY_FOR_DISPATCH: field[:1],
        State.ASSIGNED: field[:2],
        State.ONSITE: field,
        State.NEEDS_REVIEW: [*field, "set_needs_review"],
        State.CLOSED: [*field, "close_job", "draft_invoice", "send_back_invoice"],
        State.BILLING_REVIEW: [*field, "close_job", "draft_invoice"],
        State.INVOICED: [*field, "close_job", "draft_invoice", "approve_invoice"],
        State.PAID: [*field, "close_job", "draft_invoice", "approve_invoice", "record_payment"],
    }[target]
    return base + tail


def walk(commands: list[str]) -> list[tuple[str, State | None, State]]:
    """Check a path against the state table; return (command, from, to) per step."""
    steps: list[tuple[str, State | None, State]] = []
    current: State | None = None
    for command in commands:
        if not allowed(command, current):
            raise ValueError(f"{command} is not allowed from {current}")
        target = TRANSITIONS[command].target
        steps.append((command, current, target))
        current = target
    return steps


class _World:
    def __init__(self, seed: int, now: datetime) -> None:
        self.rng = random.Random(seed)
        self.now = now

    def uuid(self) -> uuid.UUID:
        return uuid.UUID(int=self.rng.getrandbits(128), version=4)

    def cents(self, low: int, high: int, step: int = 5_000) -> int:
        return self.rng.randrange(low // step, high // step + 1) * step


async def clear(session: AsyncSession) -> None:
    """Empty every table and restart the job numbers and event ids, so a reseed is identical."""
    await session.execute(
        text(
            "TRUNCATE qb_ledger, invoices, job_events, jobs, fleet_positions, techs, people, sites, contracts, "
            "clients RESTART IDENTITY CASCADE"
        )
    )


async def seed(session: AsyncSession, seed: int = DEFAULT_SEED, now: datetime | None = None) -> dict[str, int]:
    """Clear, then build the world. Returns the row counts."""
    w = _World(seed, (now or datetime.now(UTC)).replace(second=0, microsecond=0))
    await clear(session)

    clients: list[tuple[ClientSpec, Client, Contract]] = []
    sites: dict[uuid.UUID, list[Site]] = {}
    store_no = w.rng.randrange(1100, 1900)
    for spec in CLIENTS:
        client = Client(
            id=w.uuid(),
            name=spec.name,
            channel=spec.channel,
            invoice_format=spec.invoice_format,
            created_at=w.now - timedelta(days=400),
        )
        rules: list[dict[str, Any]] = [
            {
                "kind": "cap",
                "amount_cents": spec.cap_cents,
                "text": f"{spec.name}: over ${spec.cap_cents // 100:,} needs the client's approval first",
            }
        ]
        if spec.review:
            rules.append(
                {
                    "kind": "review",
                    "issue_type": spec.review,
                    "text": f"{spec.name}: {spec.review} costs need additional review",
                }
            )
        contract = Contract(
            id=w.uuid(),
            client_id=client.id,
            issue_types=list(ISSUE_TYPES),
            rules=rules,
            net_days=spec.net_days,
        )
        clients.append((spec, client, contract))
        sites[client.id] = []
        for _ in range(spec.sites):
            state = w.rng.choice(list(CITIES))
            city, lat, lng = w.rng.choice(CITIES[state])
            store_no += w.rng.randrange(3, 40)
            sites[client.id].append(
                Site(
                    id=w.uuid(),
                    client_id=client.id,
                    store_number=str(store_no),
                    label=f"{spec.name} #{store_no}, {city}",
                    address=f"{w.rng.randrange(100, 9900)} {w.rng.choice(STREETS)}",
                    city=city,
                    state=state,
                    lat=round(lat + w.rng.uniform(-0.08, 0.08), 4),
                    lng=round(lng + w.rng.uniform(-0.08, 0.08), 4),
                    contact=f"Store manager, (555) 01{w.rng.randrange(0, 100):02d}",
                )
            )
    session.add_all([c for _, c, _ in clients])
    await session.flush()
    session.add_all([k for _, _, k in clients])
    session.add_all([s for group in sites.values() for s in group])

    people: dict[str, Person] = {}

    def person(label: str, role: Role) -> Person:
        p = Person(id=w.uuid(), label=label, role=role.value, email=DEMO_LOGINS.get(label))
        people[label] = p
        return p

    coordinators = [person(f"Coordinator {i}", Role.COORDINATOR) for i in (1, 2, 3)]
    dispatcher = person("Dispatcher", Role.DISPATCHER)
    controller = person("Controller", Role.CONTROLLER)
    person("Executive", Role.EXEC)
    tech_people = [person(f"Tech {i}", Role.TECH) for i in range(1, 11)]
    session.add_all(people.values())
    await session.flush()

    techs: list[Tech] = []
    for i, tp in enumerate(tech_people):
        home_state, city = HOMES[i]
        _, lat, lng = next(c for c in CITIES[home_state] if c[0] == city)
        neighbours = NEIGHBOURS[home_state]
        skills = sorted(
            {
                ISSUE_TYPES[i % len(ISSUE_TYPES)],
                ISSUE_TYPES[(i + 3) % len(ISSUE_TYPES)],
                *w.rng.sample(ISSUE_TYPES, 3),
            }
        )
        techs.append(
            Tech(
                id=w.uuid(),
                person_id=tp.id,
                skills=skills,
                licenses=sorted([home_state, *neighbours]),
                home_city=city,
                home_lat=lat,
                home_lng=lng,
                truck=f"T-{i + 1:02d}",
            )
        )
    session.add_all(techs)
    await session.flush()
    session.add_all(
        [FleetPosition(truck=t.truck, lat=t.home_lat, lng=t.home_lng, at=w.now, status="parked") for t in techs]
    )

    def eligible(site: Site, issue: str) -> list[Tech]:
        return [t for t in techs if issue in t.skills and site.state in t.licenses]

    doc_no = 20450
    targets = [s for s, n in JOBS_BY_STATE.items() for _ in range(n)]
    for target in targets:
        while True:  # pick a job the target state makes sense for
            spec, client, contract = w.rng.choices(clients, weights=[c[0].sites for c in clients])[0]
            site = w.rng.choice(sites[client.id])
            issue = w.rng.choice(ISSUE_TYPES)
            # A few run over the client's cap (plan §7); most sit under it. Values stay in $2K to $50K.
            over = target is State.NEEDS_CLIENT_APPROVAL or w.rng.random() < 0.1
            if over:
                estimate = w.cents(min(spec.cap_cents + 100_000, 4_900_000), 5_000_000)
            else:
                estimate = w.cents(200_000, max(200_000, spec.cap_cents - 50_000))
            requires, rule = evaluate(contract.rules, issue, estimate)
            if target is State.NEEDS_CLIENT_APPROVAL and not requires:
                continue
            if target not in (
                State.INTAKE_DRAFT,
                State.QUALIFIED,
                State.NEEDS_CLIENT_APPROVAL,
            ) and not eligible(site, issue):
                continue  # dispatch always has a tech to recommend (D2)
            break

        steps = walk(path_to(target, requires))
        hours = [w.rng.uniform(*STEP_HOURS[c]) for c, _, _ in steps]
        t = w.now - timedelta(hours=sum(hours) + w.rng.uniform(0.2, 12))
        owner = w.rng.choice(coordinators)
        tech = w.rng.choice(eligible(site, issue)) if eligible(site, issue) else None
        tech_label = next(p.label for p in tech_people if tech and p.id == tech.person_id) if tech else None
        source = spec.channel
        job = Job(
            id=w.uuid(),
            client_id=client.id,
            site_id=site.id,
            client_wo=f"{spec.wo_prefix}{w.rng.randrange(100000, 999999)}",
            client_po=f"PO-{w.rng.randrange(40000, 99999)}" if spec.channel == "portal" else None,
            site_contact=site.contact,
            source=source,
            source_text=f"{spec.name} store #{site.store_number} ({site.city}, {site.state}): "
            f"{ISSUE_WORDS[issue]}. Contact the {site.contact}.",
            drafted_by="rules",
            issue_type=issue,
            parts="none",
            part_numbers=[],
            est_hours=round(w.rng.uniform(2, 12), 1),
            extenuating=[],
            requires_approval=requires,
            rule_fired=rule,
            state=target.value,
            estimate_cents=estimate,
            created_at=t,
            updated_at=t,
        )
        session.add(job)
        await session.flush()

        events: list[JobEvent] = []
        invoice: Invoice | None = None
        for (command, src, dst), h in zip(steps, hours, strict=True):
            t += timedelta(hours=h)
            kind: ActorKind = ActorKind.PERSON
            actor: Person | None = owner
            payload: dict[str, Any] = {}
            if command == "draft_intake":
                kind, actor, payload = (
                    ActorKind.SYSTEM,
                    None,
                    {"source": source, "drafted_by": "rules"},
                )
            elif command in ("assign_tech", "reassign_tech"):
                actor, payload = dispatcher, {"tech": tech_label}
                job.tech_id = tech.id if tech else None
            elif command in ("arrive", "set_needs_review", "close_job"):
                actor = next(p for p in tech_people if tech and p.id == tech.person_id)
            elif command in ("approve_invoice", "send_back_invoice"):
                actor = controller
            elif command in ("draft_invoice", "record_payment"):
                kind, actor = ActorKind.SYSTEM, None

            if command == "qualify":
                job.owner_id = owner.id
            elif command == "record_client_approval":
                ref = f"{spec.wo_prefix}APR-{w.rng.randrange(1000, 9999)}"
                job.approval = {
                    "by": "Client facilities manager",
                    "at": t.isoformat(),
                    "client_ref": ref,
                }
                payload = {"by": "Client facilities manager", "client_ref": ref}
            elif command == "assign_tech":
                start = (
                    (w.now + timedelta(hours=w.rng.uniform(0.5, 7)))
                    if target is State.ASSIGNED
                    else (t + timedelta(hours=hours[steps.index((command, src, dst)) + 1] - 0.5))
                )
                job.window_start, job.window_end = start, start + timedelta(hours=2)
            elif command == "set_needs_review":
                job.extenuating = [w.rng.choice(["parts_delay", "scope_changed", "access_denied"])]
                job.extenuating_note = "Needs a decision before the work continues"
                payload = {"reason": job.extenuating[0]}
            elif command == "close_job":
                # Whether the invoice will pass its check is decided here, the way it is in the field: a job sent
                # back (CLOSED) had no sign-off; about a quarter of those in billing review ran over the estimate;
                # anything approved passed. The check itself is the backend's own (commands.invoice_check).
                over = target is State.BILLING_REVIEW and w.rng.random() < 0.25
                job.actual_hours = round((job.est_hours or 4) * w.rng.uniform(0.7, 1.4), 1)
                factor = w.rng.uniform(1.12, 1.3) if over else w.rng.uniform(0.85, 1.05)
                job.final_cents = round(estimate * factor / 100) * 100
                job.parts = w.rng.choice(["none", "on_truck", "special_order"])
                job.part_numbers = [f"PN-{w.rng.randrange(10000, 99999)}"] if job.parts == "special_order" else []
                if target is State.CLOSED:
                    job.sign_off, job.extenuating_note = None, "Store manager not on site"
                    payload = {"actual_hours": job.actual_hours, "no_sign_off_reason": "Store manager not on site"}
                else:
                    job.sign_off = {"by": "Store manager", "at": t.isoformat()}
                    payload = {"actual_hours": job.actual_hours, "sign_off_by": "Store manager"}
            elif command == "draft_invoice":
                final = job.final_cents or estimate
                labor = round(final * 0.6 / 100) * 100
                note = invoice_check(job)
                invoice = Invoice(
                    id=w.uuid(),
                    job_id=job.id,
                    format=spec.invoice_format,
                    state="draft",
                    created_at=t,
                    lines=[
                        {"desc": f"Labor, {job.actual_hours} h", "cents": labor},
                        {"desc": "Parts and materials", "cents": final - labor},
                    ],
                    total_cents=final,
                    check_passed=note is None,
                    check_note=note,
                )
            elif command == "send_back_invoice" and invoice:
                invoice.state = "sent_back"
                payload = {"reason": invoice.check_note}
            elif command == "approve_invoice" and invoice:
                if not invoice.check_passed:  # the backend refuses this; so does the seed
                    raise ValueError(f"seed would approve a failed invoice: {invoice.check_note}")
                invoice.state, invoice.qb_doc_number = "submitted", f"QB-{doc_no}"
                payload = {"qb_doc_number": invoice.qb_doc_number}
                session.add(invoice)
                await session.flush()
                session.add(
                    QbLedger(
                        id=w.uuid(),
                        invoice_id=invoice.id,
                        client_id=client.id,
                        doc_number=invoice.qb_doc_number,
                        amount_cents=invoice.total_cents,
                        issued_at=t,
                        due_at=t + timedelta(days=spec.net_days),
                        paid_at=None,
                    )
                )
                doc_no += 1
            elif command == "record_payment":
                payload = {"qb_doc_number": invoice.qb_doc_number if invoice else None}

            events.append(
                JobEvent(
                    job_id=job.id,
                    at=t,
                    actor_kind=kind.value,
                    actor_id=actor.id if actor else None,
                    actor_label=actor.label
                    if actor
                    else ("QuickBooks (simulated)" if command == "record_payment" else "System"),
                    command=command,
                    from_state=src.value if src else None,
                    to_state=dst.value,
                    payload=payload,
                )
            )
        if target is State.PAID:
            paid_id: uuid.UUID = (
                await session.execute(
                    text("SELECT id FROM qb_ledger WHERE doc_number = :d"),
                    {"d": invoice.qb_doc_number if invoice else ""},
                )
            ).scalar_one()
            await session.execute(text("UPDATE qb_ledger SET paid_at = :t WHERE id = :i"), {"t": t, "i": paid_id})
        if invoice and invoice.state != "submitted":
            session.add(invoice)
        session.add_all(events)
        await session.flush()
        job.last_event_id = events[-1].id
        job.updated_at = events[-1].at

    # Trucks stand where their techs are working (cold review, finding 18): a tech on site has the truck at the site.
    trucks = {t.id: t.truck for t in techs}
    on_site = (
        await session.execute(select(Job, Site).join(Site, Site.id == Job.site_id).where(Job.state == "onsite"))
    ).all()
    for working, at_site in on_site:
        pos = await session.get(FleetPosition, trucks[working.tech_id]) if working.tech_id else None
        if pos:
            pos.lat, pos.lng, pos.status = at_site.lat, at_site.lng, "onsite"

    # Historical QuickBooks invoices: three open ones in every aging bucket, then the rest at random.
    ledger: list[QbLedger] = []
    for low, high in AGING_BUCKETS:
        for _ in range(3):
            spec, client, _c = w.rng.choice(clients)
            due = w.now - timedelta(days=w.rng.randint(low, high))
            ledger.append(
                QbLedger(
                    id=w.uuid(),
                    invoice_id=None,
                    client_id=client.id,
                    doc_number=f"QB-{doc_no}",
                    amount_cents=w.cents(200_000, 5_000_000),
                    issued_at=due - timedelta(days=spec.net_days),
                    due_at=due,
                    paid_at=None,
                )
            )
            doc_no += 1
    for _ in range(135):
        spec, client, _c = w.rng.choice(clients)
        issued = w.now - timedelta(days=w.rng.uniform(5, 180))
        due = issued + timedelta(days=spec.net_days)
        paid = issued + timedelta(days=w.rng.uniform(spec.net_days - 10, spec.net_days + 40))
        ledger.append(
            QbLedger(
                id=w.uuid(),
                invoice_id=None,
                client_id=client.id,
                doc_number=f"QB-{doc_no}",
                amount_cents=w.cents(200_000, 5_000_000),
                issued_at=issued,
                due_at=due,
                paid_at=paid if paid < w.now and w.rng.random() < 0.8 else None,
            )
        )
        doc_no += 1
    session.add_all(ledger)
    await session.flush()

    counts: dict[str, int] = {}
    for table in (
        "clients",
        "contracts",
        "sites",
        "people",
        "techs",
        "fleet_positions",
        "jobs",
        "job_events",
        "invoices",
        "qb_ledger",
    ):
        counts[table] = int((await session.execute(text(f"SELECT count(*) FROM {table}"))).scalar_one())
    return counts


async def _main() -> None:
    from .db import SessionFactory, engine

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    async with SessionFactory() as session:
        counts = await seed(session, args.seed)
        await session.commit()
    await engine.dispose()
    print(" ".join(f"{k}={v}" for k, v in counts.items()))


if __name__ == "__main__":
    asyncio.run(_main())
