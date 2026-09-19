from power_monitor.domain.events import FirstRunEvent
from power_monitor.domain.model import State, Timestamp


class CheckPower:
    def __init__(self, clock, pin, state_repo, notifier, system) -> None:
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
            self._state_repo.save(State(current, now))
