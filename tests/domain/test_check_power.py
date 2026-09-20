from datetime import UTC, datetime

from power_monitor.domain.check_power import CheckPower
from power_monitor.domain.errors import NotificationFailed
from power_monitor.domain.events import (
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


class FakeClock(Clock):
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


class FakePower(PowerStateReader):
    def __init__(self, state: PowerState) -> None:
        self._state = state

    def read(self) -> PowerState:
        return self._state


class InMemoryStateRepository(StateRepository):
    def __init__(self) -> None:
        self._state: State | None = None

    def load(self) -> State | None:
        return self._state

    def save(self, state: State) -> None:
        self._state = state


class SpyNotifier(Notifier):
    def __init__(self, fail: bool = False) -> None:
        self.events: list[object] = []
        self._fail = fail

    def notify(self, event: object) -> None:
        self.events.append(event)
        if self._fail:
            raise NotificationFailed()


class SpySystem(SystemCommand):
    def __init__(self) -> None:
        self.shutdown_called = False

    def shutdown(self) -> None:
        self.shutdown_called = True


def _run(
    now_dt: datetime,
    power: PowerState,
    repo: StateRepository,
    notifier: Notifier,
    system: SystemCommand,
) -> None:
    CheckPower(FakeClock(now_dt), FakePower(power), repo, notifier, system).run()


def test_first_run_with_power_on_sends_first_run_event() -> None:
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    repo = InMemoryStateRepository()
    notifier = SpyNotifier()
    system = SpySystem()

    _run(now, PowerState.ON, repo, notifier, system)

    assert notifier.events == [FirstRunEvent(PowerState.ON, Timestamp(now))]


def test_first_run_with_power_off_sends_first_run_then_power_off_and_shuts_down() -> None:
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    repo = InMemoryStateRepository()
    notifier = SpyNotifier()
    system = SpySystem()

    _run(now, PowerState.OFF, repo, notifier, system)

    assert notifier.events == [
        FirstRunEvent(PowerState.OFF, Timestamp(now)),
        PowerEvent(PowerState.OFF, Timestamp(now)),
    ]
    assert system.shutdown_called is True


def test_first_run_persists_state() -> None:
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    repo = InMemoryStateRepository()
    notifier = SpyNotifier()
    system = SpySystem()

    _run(now, PowerState.ON, repo, notifier, system)

    assert repo.load() == State(PowerState.ON, Timestamp(now))


def test_power_off_sends_power_off_and_shuts_down() -> None:
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    earlier = datetime(2025, 1, 15, 11, 55, 0, tzinfo=UTC)

    repo = InMemoryStateRepository()
    repo.save(State(PowerState.OFF, Timestamp(earlier)))
    notifier = SpyNotifier()
    system = SpySystem()

    _run(now, PowerState.OFF, repo, notifier, system)

    assert notifier.events == [PowerEvent(PowerState.OFF, Timestamp(now))]
    assert system.shutdown_called is True


def test_transition_from_off_to_on_sends_power_on() -> None:
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    earlier = datetime(2025, 1, 15, 11, 55, 0, tzinfo=UTC)

    repo = InMemoryStateRepository()
    repo.save(State(PowerState.OFF, Timestamp(earlier)))
    notifier = SpyNotifier()
    system = SpySystem()

    _run(now, PowerState.ON, repo, notifier, system)

    assert notifier.events == [PowerEvent(PowerState.ON, Timestamp(now))]
    assert system.shutdown_called is False


def test_power_on_same_month_sends_no_event() -> None:
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    earlier = datetime(2025, 1, 15, 11, 55, 0, tzinfo=UTC)

    repo = InMemoryStateRepository()
    repo.save(State(PowerState.ON, Timestamp(earlier)))
    notifier = SpyNotifier()
    system = SpySystem()

    _run(now, PowerState.ON, repo, notifier, system)

    assert notifier.events == []
    assert system.shutdown_called is False
    assert repo.load() == State(PowerState.ON, Timestamp(now))


def test_power_on_new_month_sends_heartbeat() -> None:
    now = datetime(2025, 2, 1, 12, 0, 0, tzinfo=UTC)
    earlier = datetime(2025, 1, 15, 11, 55, 0, tzinfo=UTC)

    repo = InMemoryStateRepository()
    repo.save(State(PowerState.ON, Timestamp(earlier)))
    notifier = SpyNotifier()
    system = SpySystem()

    _run(now, PowerState.ON, repo, notifier, system)

    assert notifier.events == [HeartbeatEvent(Timestamp(now))]
    assert repo.load() == State(PowerState.ON, Timestamp(now))


def test_power_off_notification_failure_does_not_advance_state_or_shutdown() -> None:
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    earlier = datetime(2025, 1, 15, 11, 55, 0, tzinfo=UTC)

    repo = InMemoryStateRepository()
    repo.save(State(PowerState.OFF, Timestamp(earlier)))
    notifier = SpyNotifier(fail=True)
    system = SpySystem()

    _run(now, PowerState.OFF, repo, notifier, system)

    assert notifier.events == [PowerEvent(PowerState.OFF, Timestamp(now))]
    assert system.shutdown_called is False
    assert repo.load() == State(PowerState.OFF, Timestamp(earlier))


def test_transition_notification_failure_does_not_advance_state() -> None:
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    earlier = datetime(2025, 1, 15, 11, 55, 0, tzinfo=UTC)

    repo = InMemoryStateRepository()
    repo.save(State(PowerState.OFF, Timestamp(earlier)))
    notifier = SpyNotifier(fail=True)
    system = SpySystem()

    _run(now, PowerState.ON, repo, notifier, system)

    assert notifier.events == [PowerEvent(PowerState.ON, Timestamp(now))]
    assert system.shutdown_called is False
    assert repo.load() == State(PowerState.OFF, Timestamp(earlier))


def test_heartbeat_notification_failure_does_not_advance_state() -> None:
    now = datetime(2025, 2, 1, 12, 0, 0, tzinfo=UTC)
    earlier = datetime(2025, 1, 15, 11, 55, 0, tzinfo=UTC)

    repo = InMemoryStateRepository()
    repo.save(State(PowerState.ON, Timestamp(earlier)))
    notifier = SpyNotifier(fail=True)
    system = SpySystem()

    _run(now, PowerState.ON, repo, notifier, system)

    assert notifier.events == [HeartbeatEvent(Timestamp(now))]
    assert system.shutdown_called is False
    assert repo.load() == State(PowerState.ON, Timestamp(earlier))


def test_first_run_notification_failure_saves_no_state() -> None:
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)

    repo = InMemoryStateRepository()
    notifier = SpyNotifier(fail=True)
    system = SpySystem()

    _run(now, PowerState.ON, repo, notifier, system)

    assert notifier.events == [FirstRunEvent(PowerState.ON, Timestamp(now))]
    assert repo.load() is None


def test_transition_takes_precedence_over_heartbeat() -> None:
    now = datetime(2025, 2, 1, 12, 0, 0, tzinfo=UTC)
    earlier = datetime(2025, 1, 15, 11, 55, 0, tzinfo=UTC)

    repo = InMemoryStateRepository()
    repo.save(State(PowerState.OFF, Timestamp(earlier)))
    notifier = SpyNotifier()
    system = SpySystem()

    _run(now, PowerState.ON, repo, notifier, system)

    assert notifier.events == [PowerEvent(PowerState.ON, Timestamp(now))]


def test_repeated_failures_retry_until_delivered() -> None:
    t1 = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    t2 = datetime(2025, 1, 15, 12, 5, 0, tzinfo=UTC)
    t3 = datetime(2025, 1, 15, 12, 10, 0, tzinfo=UTC)
    earlier = datetime(2025, 1, 15, 11, 55, 0, tzinfo=UTC)

    repo = InMemoryStateRepository()
    repo.save(State(PowerState.OFF, Timestamp(earlier)))

    notifier1 = SpyNotifier(fail=True)
    system1 = SpySystem()
    _run(t1, PowerState.OFF, repo, notifier1, system1)
    assert notifier1.events == [PowerEvent(PowerState.OFF, Timestamp(t1))]
    assert system1.shutdown_called is False
    assert repo.load() == State(PowerState.OFF, Timestamp(earlier))

    notifier2 = SpyNotifier(fail=True)
    system2 = SpySystem()
    _run(t2, PowerState.OFF, repo, notifier2, system2)
    assert notifier2.events == [PowerEvent(PowerState.OFF, Timestamp(t2))]
    assert system2.shutdown_called is False
    assert repo.load() == State(PowerState.OFF, Timestamp(earlier))

    notifier3 = SpyNotifier()
    system3 = SpySystem()
    _run(t3, PowerState.OFF, repo, notifier3, system3)
    assert notifier3.events == [PowerEvent(PowerState.OFF, Timestamp(t3))]
    assert system3.shutdown_called is True
    assert repo.load() == State(PowerState.OFF, Timestamp(t3))
