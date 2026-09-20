from pathlib import Path

from power_monitor.domain.model import State
from power_monitor.domain.ports.state_repository import StateRepository


class JsonStateRepository(StateRepository):
    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> State | None:
        if not self._path.exists():
            return None
        raise NotImplementedError

    def save(self, state: State) -> None:
        raise NotImplementedError