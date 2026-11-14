from __future__ import annotations

from ofs.rules import evaluate

RULES = [
    {"kind": "cap", "amount_cents": 2_500_000, "text": "over $25,000 needs approval"},
    {"kind": "review", "issue_type": "hvac", "text": "HVAC needs review"},
]


def test_under_the_cap_and_not_hvac_needs_nothing() -> None:
    assert evaluate(RULES, "plumbing", 2_500_000) == (False, None)


def test_over_the_cap_fires_and_says_why() -> None:
    assert evaluate(RULES, "plumbing", 2_500_001) == (True, "over $25,000 needs approval")


def test_both_rules_name_both_reasons() -> None:
    assert evaluate(RULES, "hvac", 3_000_000) == (
        True,
        "over $25,000 needs approval; HVAC needs review",
    )
