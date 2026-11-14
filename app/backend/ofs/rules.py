"""Contract rules: does this job need the client's approval before dispatch? (plan §4, page 2)

A rule that fires says why in its own words, so nobody argues with a bare flag.
"""

from __future__ import annotations

from typing import Any


def evaluate(rules: list[dict[str, Any]], issue_type: str, estimate_cents: int) -> tuple[bool, str | None]:
    fired: list[str] = []
    for rule in rules:
        if rule["kind"] == "cap" and estimate_cents > rule["amount_cents"]:
            fired.append(rule["text"])
        elif rule["kind"] == "review" and rule["issue_type"] == issue_type:
            fired.append(rule["text"])
    return (bool(fired), "; ".join(fired) or None)
