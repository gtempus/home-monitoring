from datetime import UTC, datetime

from power_monitor.domain.model import PinState, State, Timestamp
from power_monitor.domain.ports.state_repository import StateRepository


def test_load_before_any_save_returns_none(state_repo: StateRepository) -> None:
    assert state_repo.load() is None


def test_save_then_load_round_trips(state_repo: StateRepository) -> None:
    original = State(
        pin_state=PinState.HIGH,
        timestamp=Timestamp(datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)),
    )

    state_repo.save(original)

    assert state_repo.load() == original


def test_save_overwrites_previous_state(state_repo: StateRepository) -> None:
    first = State(
        pin_state=PinState.HIGH,
        timestamp=Timestamp(datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)),
    )
    second = State(
        pin_state=PinState.LOW,
        timestamp=Timestamp(datetime(2025, 1, 16, 12, 0, 0, tzinfo=UTC)),
    )

    state_repo.save(first)
    state_repo.save(second)

    assert state_repo.load() == second
