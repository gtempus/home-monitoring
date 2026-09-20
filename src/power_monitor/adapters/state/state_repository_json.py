import contextlib
import json
import os
from datetime import datetime
from pathlib import Path

from power_monitor.domain.model import PinState, State, Timestamp
from power_monitor.domain.ports.state_repository import StateRepository


class StateRepositoryError(Exception):
    """Raised when the persisted state cannot be read or trusted."""


class JsonStateRepository(StateRepository):
    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> State | None:
        if not self._path.exists():
            return None
        try:
            raw = json.loads(self._path.read_text())
        except json.JSONDecodeError as exc:
            raise StateRepositoryError(f"corrupt state file: {self._path}") from exc
        return self._deserialize(raw)

    def save(self, state: State) -> None:
        payload = {
            "pin_state": state.pin_state.name,
            "timestamp": state.timestamp.value.isoformat(),
        }
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(payload))
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, self._path)
        finally:
            with contextlib.suppress(OSError):
                tmp.unlink(missing_ok=True)

    def _deserialize(self, raw: object) -> State:
        if not isinstance(raw, dict):
            raise StateRepositoryError(
                f"state file is not a JSON object: {self._path}"
            )

        if "pin_state" not in raw:
            raise StateRepositoryError(
                f"state file missing 'pin_state': {self._path}"
            )
        pin_name = raw["pin_state"]
        if not isinstance(pin_name, str):
            raise StateRepositoryError(
                f"state file has non-string 'pin_state' ({pin_name!r}): {self._path}"
            )
        try:
            pin_state = PinState[pin_name]
        except KeyError as exc:
            raise StateRepositoryError(
                f"state file has unknown 'pin_state' ({pin_name!r}): {self._path}"
            ) from exc

        if "timestamp" not in raw:
            raise StateRepositoryError(
                f"state file missing 'timestamp': {self._path}"
            )
        raw_ts = raw["timestamp"]
        if not isinstance(raw_ts, str):
            raise StateRepositoryError(
                f"state file has non-string 'timestamp' ({raw_ts!r}): {self._path}"
            )
        try:
            timestamp = Timestamp(datetime.fromisoformat(raw_ts))
        except ValueError as exc:
            raise StateRepositoryError(
                f"state file has invalid 'timestamp' ({raw_ts!r}): {self._path}"
            ) from exc

        return State(pin_state=pin_state, timestamp=timestamp)