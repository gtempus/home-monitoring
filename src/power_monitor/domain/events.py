from dataclasses import dataclass
from enum import Enum, auto

from power_monitor.domain.model import PinState, Timestamp


@dataclass(frozen=True)
class FirstRunEvent:
    pin_state: PinState
    at: Timestamp


class PowerEventKind(Enum):
    ON = auto()
    OFF = auto()


@dataclass(frozen=True)
class PowerEvent:
    kind: PowerEventKind
    at: Timestamp


@dataclass(frozen=True)
class HeartbeatEvent:
    at: Timestamp


Event = FirstRunEvent | PowerEvent | HeartbeatEvent