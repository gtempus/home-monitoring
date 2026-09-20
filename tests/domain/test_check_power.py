from datetime import UTC, datetime

from power_monitor.domain.check_power import CheckPower
from power_monitor.domain.errors import NotificationFailed
from power_monitor.domain.events import (
    Event,
    FirstRunEvent,
    HeartbeatEvent,
    PowerEvent,
    PowerEventKind,
)
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
    def __init__(self, fail: bool = False) -> None:
        self.events: list[Event] = []
        self._fail = fail

    def notify(self, event: Event) -> None:
        self.events.append(event)
        if self._fail:
            raise NotificationFailed()


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

def test_second_run_with_high_pin_same_month_sends_no_event() -> None:
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    earlier = datetime(2025, 1, 15, 11, 55, 0, tzinfo=UTC)

    clock = FakeClock(now)
    pin = FakePin(PinState.HIGH)
    repo = InMemoryStateRepository()
    repo.save(State(PinState.HIGH, Timestamp(earlier)))  # previous run saw HIGH
    notifier = SpyNotifier()
    system = SpySystem()

    CheckPower(clock, pin, repo, notifier, system).run()

    assert notifier.events == []
    assert system.shutdown_called is False
    assert repo.load() == State(PinState.HIGH, Timestamp(now))

def test_second_run_with_high_pin_new_month_sends_heartbeat() -> None:
    now = datetime(2025, 2, 1, 12, 0, 0, tzinfo=UTC)
    earlier = datetime(2025, 1, 15, 11, 55, 0, tzinfo=UTC)  # previous month

    clock = FakeClock(now)
    pin = FakePin(PinState.HIGH)
    repo = InMemoryStateRepository()
    repo.save(State(PinState.HIGH, Timestamp(earlier)))
    notifier = SpyNotifier()
    system = SpySystem()

    CheckPower(clock, pin, repo, notifier, system).run()

    assert notifier.events == [HeartbeatEvent(Timestamp(now))]
    assert repo.load() == State(PinState.HIGH, Timestamp(now))

def test_low_path_notification_failure_does_not_advance_state_or_shutdown() -> None:
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    earlier = datetime(2025, 1, 15, 11, 55, 0, tzinfo=UTC)

    clock = FakeClock(now)
    pin = FakePin(PinState.LOW)
    repo = InMemoryStateRepository()
    repo.save(State(PinState.LOW, Timestamp(earlier)))
    notifier = SpyNotifier(fail=True)
    system = SpySystem()

    CheckPower(clock, pin, repo, notifier, system).run()

    assert notifier.events == [PowerEvent(PowerEventKind.OFF, Timestamp(now))]
    assert system.shutdown_called is False
    assert repo.load() == State(PinState.LOW, Timestamp(earlier))  # unchanged

def test_high_transition_notification_failure_does_not_advance_state() -> None:
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    earlier = datetime(2025, 1, 15, 11, 55, 0, tzinfo=UTC)

    clock = FakeClock(now)
    pin = FakePin(PinState.HIGH)
    repo = InMemoryStateRepository()
    repo.save(State(PinState.LOW, Timestamp(earlier)))  # previous run saw LOW
    notifier = SpyNotifier(fail=True)
    system = SpySystem()

    CheckPower(clock, pin, repo, notifier, system).run()

    assert notifier.events == [PowerEvent(PowerEventKind.ON, Timestamp(now))]
    assert system.shutdown_called is False
    assert repo.load() == State(PinState.LOW, Timestamp(earlier))  # unchanged

def test_heartbeat_notification_failure_does_not_advance_state() -> None:
    now = datetime(2025, 2, 1, 12, 0, 0, tzinfo=UTC)
    earlier = datetime(2025, 1, 15, 11, 55, 0, tzinfo=UTC)  # previous month

    clock = FakeClock(now)
    pin = FakePin(PinState.HIGH)
    repo = InMemoryStateRepository()
    repo.save(State(PinState.HIGH, Timestamp(earlier)))
    notifier = SpyNotifier(fail=True)
    system = SpySystem()

    CheckPower(clock, pin, repo, notifier, system).run()

    assert notifier.events == [HeartbeatEvent(Timestamp(now))]
    assert system.shutdown_called is False
    assert repo.load() == State(PinState.HIGH, Timestamp(earlier))  # unchanged

def test_first_run_notification_failure_saves_no_state() -> None:
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)

    clock = FakeClock(now)
    pin = FakePin(PinState.HIGH)
    repo = InMemoryStateRepository()
    notifier = SpyNotifier(fail=True)
    system = SpySystem()

    CheckPower(clock, pin, repo, notifier, system).run()

    assert notifier.events == [FirstRunEvent(PinState.HIGH, Timestamp(now))]
    assert repo.load() is None  # nothing saved

def test_transition_takes_precedence_over_heartbeat() -> None:
    now = datetime(2025, 2, 1, 12, 0, 0, tzinfo=UTC)
    earlier = datetime(2025, 1, 15, 11, 55, 0, tzinfo=UTC)

    clock = FakeClock(now)
    pin = FakePin(PinState.HIGH)
    repo = InMemoryStateRepository()
    repo.save(State(PinState.LOW, Timestamp(earlier)))
    notifier = SpyNotifier()
    system = SpySystem()

    CheckPower(clock, pin, repo, notifier, system).run()

    assert notifier.events == [PowerEvent(PowerEventKind.ON, Timestamp(now))]

def test_repeated_failures_retry_until_delivered() -> None:
    t1 = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    t2 = datetime(2025, 1, 15, 12, 5, 0, tzinfo=UTC)
    t3 = datetime(2025, 1, 15, 12, 10, 0, tzinfo=UTC)
    earlier = datetime(2025, 1, 15, 11, 55, 0, tzinfo=UTC)

    pin = FakePin(PinState.LOW)
    repo = InMemoryStateRepository()
    repo.save(State(PinState.LOW, Timestamp(earlier)))

    # Run 1 — delivery fails
    notifier1 = SpyNotifier(fail=True)
    system1 = SpySystem()
    CheckPower(FakeClock(t1), pin, repo, notifier1, system1).run()
    assert notifier1.events == [PowerEvent(PowerEventKind.OFF, Timestamp(t1))]
    assert system1.shutdown_called is False
    assert repo.load() == State(PinState.LOW, Timestamp(earlier))

    # Run 2 — delivery fails again
    notifier2 = SpyNotifier(fail=True)
    system2 = SpySystem()
    CheckPower(FakeClock(t2), pin, repo, notifier2, system2).run()
    assert notifier2.events == [PowerEvent(PowerEventKind.OFF, Timestamp(t2))]
    assert system2.shutdown_called is False
    assert repo.load() == State(PinState.LOW, Timestamp(earlier))

    # Run 3 — delivery succeeds
    notifier3 = SpyNotifier()
    system3 = SpySystem()
    CheckPower(FakeClock(t3), pin, repo, notifier3, system3).run()
    assert notifier3.events == [PowerEvent(PowerEventKind.OFF, Timestamp(t3))]
    assert system3.shutdown_called is True
    assert repo.load() == State(PinState.LOW, Timestamp(t3))