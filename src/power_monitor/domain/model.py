from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto


class PowerState(Enum):
    ON = auto()
    OFF = auto()


@dataclass(frozen=True)
class Timestamp:
    value: datetime


@dataclass(frozen=True)
class State:
    power_state: PowerState
    timestamp: Timestamp
