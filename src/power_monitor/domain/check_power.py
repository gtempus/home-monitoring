from power_monitor.domain.errors import NotificationFailed
from power_monitor.domain.events import (
    Event,
    FirstRunEvent,
    HeartbeatEvent,
    PowerEvent,
)
from power_monitor.domain.model import PowerState, State, Timestamp
from power_monitor.domain.ports.clock import Clock
from power_monitor.domain.ports.notifier import Notifier
from power_monitor.domain.ports.power_state_reader import PowerStateReader
from power_monitor.domain.ports.state_repository import StateRepository
from power_monitor.domain.ports.system_command import SystemCommand


class CheckPower:
    def __init__(
        self,
        clock: Clock,
        power_state_reader: PowerStateReader,
        state_repo: StateRepository,
        notifier: Notifier,
        system: SystemCommand,
    ) -> None:
        self._clock = clock
        self._reader = power_state_reader
        self._state_repo = state_repo
        self._notifier = notifier
        self._system = system

    def run(self) -> None:
        now = Timestamp(self._clock.now())
        previous = self._state_repo.load()
        current = self._reader.read()

        if previous is None:
            try:
                self._notifier.notify(FirstRunEvent(current, now))
            except NotificationFailed:
                return
            if current is PowerState.OFF:
                self._handle_off(now)
            else:
                self._state_repo.save(State(PowerState.ON, now))
            return

        if current is PowerState.OFF:
            self._handle_off(now)
            return

        event = self._on_event(previous, now)
        if event is not None:
            try:
                self._notifier.notify(event)
            except NotificationFailed:
                return

        self._state_repo.save(State(PowerState.ON, now))

    def _handle_off(self, now: Timestamp) -> None:
        try:
            self._notifier.notify(PowerEvent(PowerState.OFF, now))
        except NotificationFailed:
            return
        self._state_repo.save(State(PowerState.OFF, now))
        self._system.shutdown()

    def _on_event(self, previous: State, now: Timestamp) -> Event | None:
        if previous.power_state is PowerState.OFF:
            return PowerEvent(PowerState.ON, now)
        if previous.timestamp.value.month != now.value.month:
            return HeartbeatEvent(now)
        return None
