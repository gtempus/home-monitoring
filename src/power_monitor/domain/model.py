from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto


class PinState(Enum):
    LOW = auto()
    HIGH = auto()


@dataclass(frozen=True)
class Timestamp:
    value: datetime


@dataclass(frozen=True)
class State:
    pin_state: PinState
    timestamp: Timestamp