"""Synthetic requests, as they arrive (plan §7): a portal record, a store email, a FacilIT ticket.

Nothing here is real. The simulator writes these; Claude (or the rules) drafts a job from them. The three shapes
differ the way round 4 described the doors differing: Bullseye's portal is structured, store emails are prose, and
FacilIT tickets sit in between.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

ISSUE_PHRASES: dict[str, list[str]] = {
    "hvac": ["the rooftop unit isn't cooling", "no heat on the sales floor", "the AC is blowing warm air"],
    "refrigeration": ["the walk-in cooler is above temperature", "a reach-in freezer is iced over"],
    "electrical": ["a breaker keeps tripping on the sales floor", "outlets are dead at the registers"],
    "plumbing": ["the restroom sink is leaking under the counter", "a floor drain is backing up"],
    "doors_locks": ["the front entrance door won't lock", "the rear door closer is broken"],
    "lighting": ["the parking lot lights are out", "half the ceiling lights over aisle 4 are dark"],
    "roofing": ["the roof is leaking over the stockroom", "water is coming through a ceiling tile"],
    "general": ["shelving in the back room collapsed", "a display case glass is cracked"],
}


@dataclass(frozen=True)
class SiteRef:
    client_name: str
    channel: str
    wo_prefix: str
    store_number: str
    city: str
    state: str
    contact: str


@dataclass(frozen=True)
class Source:
    channel: str
    text: str
    truth: dict[str, str | None]  # what a perfect draft would say: for tests and the eval, never shown to Claude


def make(rng: random.Random, site: SiteRef) -> Source:
    issue = rng.choice(list(ISSUE_PHRASES))
    phrase = rng.choice(ISSUE_PHRASES[issue])
    wo = f"{site.wo_prefix}{rng.randrange(100000, 999999)}"
    po = f"PO-{rng.randrange(40000, 99999)}" if site.channel == "portal" else None
    truth = {
        "client_name": site.client_name,
        "store_number": site.store_number,
        "client_wo": wo,
        "client_po": po,
        "site_contact": site.contact,
        "issue_type": issue,
    }
    if site.channel == "portal":
        text = (
            f"{site.client_name.upper()} FACILITIES PORTAL: NEW WORK ORDER\n"
            f"Work order: {wo}\nPurchase order: {po}\nStore: #{site.store_number} ({site.city}, {site.state})\n"
            f"Trade: {issue.replace('_', ' / ').upper()}\nProblem: {phrase[0].upper()}{phrase[1:]}.\n"
            f"Site contact: {site.contact}\nNot to exceed: per contract"
        )
    elif site.channel == "email":
        text = (
            f"From: {site.contact.split(',')[0]}, {site.client_name} #{site.store_number}\n"
            f"Subject: Service needed at {site.city}\n\n"
            f"Hi, {phrase} since this morning. Our reference number is {wo}. "
            f"Can someone get out here soon? Reach me at {site.contact.split(', ')[1]}.\n\nThanks"
        )
    else:
        text = (
            f"FacilIT ticket | Customer: {site.client_name} | Location #{site.store_number}, {site.city} {site.state}\n"
            f"Ref: {wo}\nRequested by: {site.contact}\nDetails: {phrase}."
        )
    return Source(channel=site.channel, text=text, truth=truth)
