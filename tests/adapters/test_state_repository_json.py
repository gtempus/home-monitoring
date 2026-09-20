from datetime import UTC
from pathlib import Path

from power_monitor.adapters.state.state_repository_json import JsonStateRepository


def test_load_returns_none_when_file_missing(tmp_path: Path) -> None:
    repo = JsonStateRepository(tmp_path / "state.json")
    assert repo.load() is None

def test_save_then_load_round_trips(tmp_path: Path) -> None:
    from datetime import datetime

    from power_monitor.domain.model import PinState, State, Timestamp

    repo = JsonStateRepository(tmp_path / "state.json")
    ts = Timestamp(datetime(2025, 1, 15, 12, 0, tzinfo=UTC))
    original = State(pin_state=PinState.HIGH, timestamp=ts)

    repo.save(original)

    assert repo.load() == original