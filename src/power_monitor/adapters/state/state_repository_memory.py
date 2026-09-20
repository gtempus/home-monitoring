from power_monitor.domain.model import State
from power_monitor.domain.ports.state_repository import StateRepository


class InMemoryStateRepository(StateRepository):
    def __init__(self) -> None:
        self._state: State | None = None

    def load(self) -> State | None:
        return self._state

    def save(self, state: State) -> None:
        self._state = state