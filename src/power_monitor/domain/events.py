from dataclasses import dataclass

from power_monitor.domain.model import PinState, Timestamp


@dataclass(frozen=True)
class FirstRunEvent:
    pin_state: PinState
    at: Timestamp