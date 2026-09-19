from typing import Protocol

from power_monitor.domain.model import State


class StateRepository(Protocol):
    def load(self) -> State | None: ...
    def save(self, state: State) -> None: ...