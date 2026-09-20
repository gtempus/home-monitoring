from typing import Protocol

from power_monitor.domain.model import PowerState


class PowerStateReader(Protocol):
    def read(self) -> PowerState: ...
