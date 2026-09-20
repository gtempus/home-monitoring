from pathlib import Path

from power_monitor.adapters.state.state_repository_json import JsonStateRepository


def test_load_returns_none_when_file_missing(tmp_path: Path) -> None:
    repo = JsonStateRepository(tmp_path / "state.json")
    assert repo.load() is None