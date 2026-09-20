from typing import Protocol

from power_monitor.domain.model import PinState
from power_monitor.domain.ports.pin_reader import PinReader


class PinReaderError(Exception):
    """Raised when the GPIO line cannot be read."""


class LineRequestLike(Protocol):
    def get_value(self, offset: int) -> object: ...


class LibGpiodPinReader(PinReader):
    def __init__(
            self,
            request: LineRequestLike,
            offset: int,
            active: object,
    ) -> None:
        self._request = request
        self._offset = offset
        self._active = active

    def read(self) -> PinState:
        try:
            value = self._request.get_value(self._offset)
        except OSError as exc:
            raise PinReaderError(
                f"failed to read GPIO line {self._offset}"
            ) from exc
        return PinState.HIGH if value == self._active else PinState.LOW