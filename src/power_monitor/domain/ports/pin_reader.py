from typing import Protocol

from power_monitor.domain.model import PinState


class PinReader(Protocol):
    def read(self) -> PinState: ...