from typing import Protocol

from power_monitor.domain.model import PowerState
from power_monitor.domain.ports.power_state_reader import PowerStateReader


class PowerStateReaderError(Exception):
    """Raised when the GPIO line cannot be read."""


class LineRequestLike(Protocol):
    def get_value(self, offset: int) -> object: ...


class LibGpiodPowerStateReader(PowerStateReader):
    def __init__(
        self,
        request: LineRequestLike,
        offset: int,
        on_value: object,
    ) -> None:
        self._request = request
        self._offset = offset
        self._on_value = on_value

    def read(self) -> PowerState:
        try:
            value = self._request.get_value(self._offset)
        except OSError as exc:
            raise PowerStateReaderError(f"failed to read GPIO line {self._offset}") from exc
        return PowerState.ON if value == self._on_value else PowerState.OFF
