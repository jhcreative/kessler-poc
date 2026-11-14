"""The state table itself: every state is reachable, every state has a queue, the happy path is legal."""

from __future__ import annotations

from ofs.seed import path_to, walk
from ofs.states import HAPPY_PATH, QUEUE, TRANSITIONS, State, allowed


def test_every_state_is_reachable_and_queued() -> None:
    reached = {t.target for t in TRANSITIONS.values()}
    assert reached == set(State)
    assert set(QUEUE) == set(State)


def test_happy_path_is_legal_and_ends_paid() -> None:
    assert walk(list(HAPPY_PATH))[-1][2] is State.PAID


def test_every_seed_path_is_legal() -> None:
    for target in State:
        for approval in (False, True):
            assert walk(path_to(target, approval))[-1][2] is target


def test_illegal_moves_are_refused() -> None:
    assert not allowed("close_job", State.ASSIGNED)  # no close without arriving
    assert not allowed("approve_invoice", State.CLOSED)  # no approval before a draft
    assert not allowed("qualify", None)
    assert not allowed("no_such_command", State.QUALIFIED)
