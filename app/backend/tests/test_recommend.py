"""Jen's eval for the recommendation (D2, test strategy): 20 cases whose answers were worked out by hand, from a map
and the rule (skill and license filter, then km + 40 per job on the board), before the code ran.

Hand distances, straight line: Allentown to Trenton about 73 km, Allentown to Harrisburg about 125 km, Harrisburg to
Baltimore about 111 km.
"""

from __future__ import annotations

import pytest

from ofs.recommend import LOAD_KM, Place, TechIn, km, recommend

ALLENTOWN = Place(40.60, -75.47, "PA")
TRENTON = Place(40.22, -74.76, "NJ")
BALTIMORE = Place(39.29, -76.61, "MD")
HARRISBURG = (40.27, -76.88)


def tech(label: str, at: tuple[float, float], skills: set[str], licenses: set[str], load: int = 0) -> TechIn:
    return TechIn(label, label, frozenset(skills), frozenset(licenses), f"T-{label}", at[0], at[1], load)


def crew(a_load: int = 0, d_load: int = 0, a_skills: set[str] | None = None) -> list[TechIn]:
    return [
        tech("A", (40.60, -75.47), a_skills or {"hvac"}, {"PA"}, a_load),  # Allentown
        tech("B", HARRISBURG, {"hvac", "plumbing"}, {"PA", "MD"}),  # Harrisburg
        tech("C", (40.22, -74.76), {"hvac"}, {"NJ", "PA"}),  # Trenton
        tech("D", (39.29, -76.61), {"plumbing"}, {"MD"}, d_load),  # Baltimore
    ]


def top(issue: str, site: Place, techs: list[TechIn]) -> str | None:
    ranked = recommend(issue, site, techs)
    return ranked[0].tech.label if ranked and ranked[0].eligible else None


@pytest.mark.parametrize(
    ("case", "issue", "site", "techs", "expected"),
    [
        (1, "hvac", ALLENTOWN, crew(), "A"),  # on the spot
        (2, "hvac", ALLENTOWN, crew(a_load=1), "A"),  # 0 + 40 beats 73
        (3, "hvac", ALLENTOWN, crew(a_load=2), "C"),  # 0 + 80 loses to 73
        (4, "plumbing", ALLENTOWN, crew(), "B"),  # D has the skill but no PA license
        (5, "electrical", ALLENTOWN, crew(), None),  # nobody has the skill: no recommendation
        (6, "hvac", TRENTON, crew(), "C"),  # only C holds NJ
        (7, "hvac", BALTIMORE, crew(), "B"),  # MD license plus hvac: only B
        (8, "plumbing", BALTIMORE, crew(), "D"),  # 0 km beats 111
        (9, "plumbing", BALTIMORE, crew(d_load=3), "B"),  # 0 + 120 loses to 111
        (10, "hvac", ALLENTOWN, crew(a_skills={"plumbing"}), "C"),  # the closest can't: next by distance
    ],
)
def test_the_recommendation_matches_the_hand_answer(
    case: int, issue: str, site: Place, techs: list[TechIn], expected: str | None
) -> None:
    assert top(issue, site, techs) == expected, f"case {case}"


def test_11_the_hand_distances_hold() -> None:
    assert 110 < km(40.60, -75.47, *HARRISBURG) < 140
    assert 65 < km(40.60, -75.47, 40.22, -74.76) < 80


def test_12_a_tech_missing_both_says_both() -> None:
    c = recommend("hvac", TRENTON, [tech("D", (39.29, -76.61), {"plumbing"}, {"MD"})])[0]
    assert not c.eligible and c.gaps == ["No hvac skill", "Not licensed in NJ"] and c.score is None


def test_13_the_reasons_name_the_skill_the_license_and_the_truck() -> None:
    c = recommend("hvac", ALLENTOWN, crew(), issue_label="HVAC")[0]
    assert c.reasons[:2] == ["Has the HVAC skill", "Licensed in PA"]
    assert c.reasons[2].startswith("Truck T-A is 0 km away")


def test_14_the_load_reads_naturally() -> None:
    reasons = [
        recommend("hvac", ALLENTOWN, [tech("A", (40.6, -75.47), {"hvac"}, {"PA"}, n)])[0].reasons[3] for n in (0, 1, 2)
    ]
    assert reasons == ["Nothing else on the board", "1 job on the board", "2 jobs on the board"]


def test_15_everyone_comes_back_the_eligible_first() -> None:
    ranked = recommend("hvac", ALLENTOWN, crew())
    assert [c.tech.label for c in ranked] == ["A", "C", "B", "D"]
    assert [c.eligible for c in ranked] == [True, True, True, False]


def test_16_the_score_is_distance_plus_load() -> None:
    c = recommend("hvac", ALLENTOWN, [tech("C", (40.22, -74.76), {"hvac"}, {"PA"}, 2)])[0]
    assert c.score == pytest.approx(c.distance_km + 2 * LOAD_KM, abs=0.2)


def test_17_no_techs_no_answer() -> None:
    assert recommend("hvac", ALLENTOWN, []) == []


def test_18_a_tie_goes_to_the_label() -> None:
    twins = [tech("Tech 3", (40.6, -75.47), {"hvac"}, {"PA"}), tech("Tech 2", (40.6, -75.47), {"hvac"}, {"PA"})]
    assert top("hvac", ALLENTOWN, twins) == "Tech 2"


def test_19_same_place_lower_load_first() -> None:
    pair = [tech("X", (40.6, -75.47), {"hvac"}, {"PA"}, 1), tech("Y", (40.6, -75.47), {"hvac"}, {"PA"}, 0)]
    assert top("hvac", ALLENTOWN, pair) == "Y"


def test_20_the_license_is_for_the_sites_state_not_the_techs_home() -> None:
    lives_in_pa = tech("H", (40.6, -75.47), {"hvac"}, {"NJ"})  # parked in Allentown, licensed only in NJ
    assert top("hvac", ALLENTOWN, [lives_in_pa]) is None
    assert top("hvac", TRENTON, [lives_in_pa]) == "H"
