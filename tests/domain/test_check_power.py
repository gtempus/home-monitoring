from datetime import UTC, datetime

from power_monitor.domain.check_power import CheckPower
from power_monitor.domain.events import Event, FirstRunEvent, PowerEvent, PowerEventKind
from power_monitor.domain.model import PinState, State, Timestamp


class FakeClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


class FakePin:
    def __init__(self, state: PinState) -> None:
        self._state = state

    def read(self) -> PinState:
        return self._state


class InMemoryStateRepository:
    def __init__(self) -> None:
        self._state: State | None = None

    def load(self) -> State | None:
        return self._state

    def save(self, state: State) -> None:
        self._state = state


class SpyNotifier:
    def __init__(self) -> None:
        self.events: list[Event] = []

    def notify(self, event: Event) -> None:
        self.events.append(event)


class SpySystem:
    def __init__(self) -> None:
        self.shutdown_called = False

    def shutdown(self) -> None:
        self.shutdown_called = True


# --- The test ---

def test_first_run_with_high_pin_sends_first_run_event() -> None:
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    clock = FakeClock(now)
    pin = FakePin(PinState.HIGH)
    repo = InMemoryStateRepository()
    notifier = SpyNotifier()
    system = SpySystem()

    CheckPower(clock, pin, repo, notifier, system).run()

    assert notifier.events == [FirstRunEvent(PinState.HIGH, Timestamp(now))]

def test_first_run_with_low_pin_sends_first_run_then_power_off_and_shuts_down() -> None:
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    clock = FakeClock(now)
    pin = FakePin(PinState.LOW)
    repo = InMemoryStateRepository()
    notifier = SpyNotifier()
    system = SpySystem()

    CheckPower(clock, pin, repo, notifier, system).run()

    assert notifier.events == [
        FirstRunEvent(PinState.LOW, Timestamp(now)),
        PowerEvent(PowerEventKind.OFF, Timestamp(now)),
    ]
    assert system.shutdown_called is True

def test_first_run_persists_state() -> None:
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    clock = FakeClock(now)
    pin = FakePin(PinState.HIGH)
    repo = InMemoryStateRepository()
    notifier = SpyNotifier()
    system = SpySystem()

    CheckPower(clock, pin, repo, notifier, system).run()

    assert repo.load() == State(PinState.HIGH, Timestamp(now))

def test_second_run_with_low_pin_sends_power_off_and_shuts_down() -> None:
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    earlier = datetime(2025, 1, 15, 11, 55, 0, tzinfo=UTC)

    clock = FakeClock(now)
    pin = FakePin(PinState.LOW)
    repo = InMemoryStateRepository()
    repo.save(State(PinState.LOW, Timestamp(earlier)))  # simulate a prior run
    notifier = SpyNotifier()
    system = SpySystem()

    CheckPower(clock, pin, repo, notifier, system).run()

    assert notifier.events == [PowerEvent(PowerEventKind.OFF, Timestamp(now))]
    assert system.shutdown_called is True

def test_second_run_with_high_pin_after_low_sends_power_on() -> None:
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    earlier = datetime(2025, 1, 15, 11, 55, 0, tzinfo=UTC)

    clock = FakeClock(now)
    pin = FakePin(PinState.HIGH)
    repo = InMemoryStateRepository()
    repo.save(State(PinState.LOW, Timestamp(earlier)))  # previous run saw LOW
    notifier = SpyNotifier()
    system = SpySystem()

    CheckPower(clock, pin, repo, notifier, system).run()

    assert notifier.events == [PowerEvent(PowerEventKind.ON, Timestamp(now))]
    assert system.shutdown_called is False