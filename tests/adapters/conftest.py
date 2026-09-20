from pathlib import Path

import pytest

from power_monitor.adapters.state.state_repository_json import JsonStateRepository
from power_monitor.adapters.state.state_repository_memory import InMemoryStateRepository
from power_monitor.domain.ports.state_repository import StateRepository


@pytest.fixture(params=["json", "memory"])
def state_repo(request: pytest.FixtureRequest, tmp_path: Path) -> StateRepository:
    if request.param == "json":
        return JsonStateRepository(tmp_path / "state.json")
    return InMemoryStateRepository()