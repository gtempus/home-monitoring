from power_monitor.domain.ports.clock import Clock
from power_monitor.domain.ports.notifier import Notifier
from power_monitor.domain.ports.system_command import SystemCommand

from power_monitor.domain.events import FirstRunEvent, PowerEvent, PowerEventKind
from power_monitor.domain.model import PinState, State, Timestamp

from power_monitor.domain.ports.pin_reader import PinReader

from power_monitor.domain.ports.state_repository import StateRepository


class CheckPower:
    def __init__(self,
                 clock: Clock,
                 pin: PinReader,
                 state_repo: StateRepository,
                 notifier:Notifier,
                 system: SystemCommand) -> None:
        self._clock = clock
        self._pin = pin
        self._state_repo = state_repo
        self._notifier = notifier
        self._system = system

    def run(self) -> None:
        now = Timestamp(self._clock.now())
        previous = self._state_repo.load()
        current = self._pin.read()

        if previous is None:
            self._notifier.notify(FirstRunEvent(current, now))
            if current is PinState.LOW:
                self._notifier.notify(PowerEvent(PowerEventKind.OFF, now))
                self._state_repo.save(State(PinState.LOW, now))
                self._system.shutdown()
            else:
                self._state_repo.save(State(PinState.HIGH, now))
            return

