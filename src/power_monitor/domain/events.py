from dataclasses import dataclass

from power_monitor.domain.model import PowerState, Timestamp


@dataclass(frozen=True)
class FirstRunEvent:
    power_state: PowerState
    at: Timestamp


@dataclass(frozen=True)
class PowerEvent:
    state: PowerState
    at: Timestamp


@dataclass(frozen=True)
class HeartbeatEvent:
    at: Timestamp


Event = FirstRunEvent | PowerEvent | HeartbeatEvent
