"""Which tech should take this job (D2, plan §7): a transparent score, with the reasons shown.

Two hard filters, both from the contract world, not preference:
1. the tech has the skill for the job's issue type;
2. the tech holds a trade license in the site's state.

Then rank the techs who pass, lowest score first:

    score = distance from the tech's truck to the site, in km + LOAD_KM for each job already on their board

A job on the board (assigned, onsite or needs review) costs as much as driving LOAD_KM further, so a nearby tech with
a full day can lose to one a little further out with nothing on. Ties go to the lower load, then the label. Every
tech is returned, those who fail a filter included, with why: dispatch can still pick one, and the soft rail asks for
a reason (commands.py).

Pure: no database, no clock. The endpoint gathers the inputs; tests/test_recommend.py holds Jen's 20 hand-checked cases.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

LOAD_KM = 40.0


@dataclass(frozen=True)
class Place:
    lat: float
    lng: float
    state: str


@dataclass(frozen=True)
class TechIn:
    id: str
    label: str
    skills: frozenset[str]
    licenses: frozenset[str]
    truck: str
    lat: float
    lng: float
    load: int


@dataclass(frozen=True)
class Candidate:
    tech: TechIn
    eligible: bool
    distance_km: float
    score: float | None  # None when not eligible
    reasons: list[str] = field(default_factory=list)  # why it fits, in words
    gaps: list[str] = field(default_factory=list)  # why it doesn't


def km(a_lat: float, a_lng: float, b_lat: float, b_lng: float) -> float:
    """Great-circle distance (haversine). Straight line, not road miles: the reasons say so."""
    r = 6371.0
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dp, dl = p2 - p1, math.radians(b_lng - a_lng)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def _natural(label: str) -> tuple[str, int]:
    """ "Tech 2" before "Tech 10" (cold review, finding 19)."""
    head, _, tail = label.rpartition(" ")
    return (head, int(tail)) if tail.isdigit() else (label, 0)


def recommend(issue_type: str, site: Place, techs: list[TechIn], issue_label: str | None = None) -> list[Candidate]:
    """Every tech, the eligible ones first by score; the first one is the recommendation."""
    label = issue_label or issue_type
    out: list[Candidate] = []
    for t in techs:
        d = km(t.lat, t.lng, site.lat, site.lng)
        gaps = []
        if issue_type not in t.skills:
            gaps.append(f"No {label} skill")
        if site.state not in t.licenses:
            gaps.append(f"Not licensed in {site.state}")
        reasons = []
        if not gaps:
            reasons = [
                f"Has the {label} skill",
                f"Licensed in {site.state}",
                f"Truck {t.truck} is {round(d)} km away in a straight line",
                "Nothing else on the board" if t.load == 0 else f"{t.load} job{'s' if t.load > 1 else ''} on the board",
            ]
        score = round(d + LOAD_KM * t.load, 1) if not gaps else None
        out.append(
            Candidate(tech=t, eligible=not gaps, distance_km=round(d, 1), score=score, reasons=reasons, gaps=gaps)
        )
    out.sort(
        key=lambda c: (
            not c.eligible,
            c.score if c.score is not None else c.distance_km,
            c.tech.load,
            _natural(c.tech.label),
        )
    )
    return out
