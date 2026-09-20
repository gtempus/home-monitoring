import json
from datetime import datetime
from pathlib import Path

from power_monitor.domain.model import PinState, State, Timestamp
from power_monitor.domain.ports.state_repository import StateRepository


class JsonStateRepository(StateRepository):
    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> State | None:
        if not self._path.exists():
            return None
        raw = json.loads(self._path.read_text())
        return State(
            pin_state=PinState[raw["pin_state"]],
            timestamp=Timestamp(datetime.fromisoformat(raw["timestamp"])),
        )

    def save(self, state: State) -> None:
        payload = {
            "pin_state": state.pin_state.name,
            "timestamp": state.timestamp.value.isoformat(),
        }
        self._path.write_text(json.dumps(payload))