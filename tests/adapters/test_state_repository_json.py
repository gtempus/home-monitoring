from datetime import UTC
from pathlib import Path

import pytest

from power_monitor.adapters.state.state_repository_json import (
    JsonStateRepository,
    StateRepositoryError,
)


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

def test_load_raises_on_corrupted_file(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    path.write_text("{not json")

    repo = JsonStateRepository(path)

    with pytest.raises(StateRepositoryError):
        repo.load()

def test_load_raises_on_non_object_json(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    path.write_text("[]")
    with pytest.raises(StateRepositoryError):
        JsonStateRepository(path).load()


def test_load_raises_on_missing_timestamp(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    path.write_text('{"pin_state": "HIGH"}')
    with pytest.raises(StateRepositoryError, match=r"missing 'timestamp'"):
        JsonStateRepository(path).load()

def test_load_raises_on_missing_pin_state(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    path.write_text('{"timestamp": "2025-01-15T12:00:00+00:00"}')
    with pytest.raises(StateRepositoryError, match=r"missing 'pin_state'"):
        JsonStateRepository(path).load()

def test_load_raises_on_unknown_pin_state(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    path.write_text('{"pin_state": "WOBBLY", "timestamp": "2025-01-15T12:00:00+00:00"}')
    with pytest.raises(StateRepositoryError, match=r"'WOBBLY'"):
        JsonStateRepository(path).load()

def test_load_raises_on_unparseable_timestamp(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    path.write_text('{"pin_state": "HIGH", "timestamp": "not-a-date"}')
    with pytest.raises(StateRepositoryError, match=r"'not-a-date'"):
        JsonStateRepository(path).load()

def test_load_raises_on_non_string_pin_state(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    path.write_text('{"pin_state": 42, "timestamp": "2025-01-15T12:00:00+00:00"}')
    with pytest.raises(StateRepositoryError, match=r"'pin_state'"):
        JsonStateRepository(path).load()

def test_load_raises_on_non_string_timestamp(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    path.write_text('{"pin_state": "HIGH", "timestamp": 42}')
    with pytest.raises(StateRepositoryError, match=r"'timestamp'"):
        JsonStateRepository(path).load()

def test_load_tolerates_extra_keys(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    path.write_text(
        '{"pin_state": "HIGH", '
        '"timestamp": "2025-01-15T12:00:00+00:00", '
        '"future_field": 42}'
    )
    assert JsonStateRepository(path).load() is not None