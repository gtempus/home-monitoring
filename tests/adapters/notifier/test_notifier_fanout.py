from datetime import UTC, datetime

import pytest

from power_monitor.adapters.notifier.notifier_fanout import FanOutNotifier
from power_monitor.domain.errors import NotificationFailed
from power_monitor.domain.events import PowerEvent
from power_monitor.domain.model import PowerState, Timestamp


class RecordingNotifier:
    def __init__(self, fail: bool = False) -> None:
        self.events: list[object] = []
        self._fail = fail

    def notify(self, event: object) -> None:
        self.events.append(event)
        if self._fail:
            raise NotificationFailed()


def _event() -> PowerEvent:
    return PowerEvent(
        PowerState.OFF,
        Timestamp(datetime(2026, 9, 20, 20, 40, 1, tzinfo=UTC)),
    )


def test_forwards_event_to_all_children() -> None:
    a = RecordingNotifier()
    b = RecordingNotifier()
    notifier = FanOutNotifier([a, b])
    event = _event()

    notifier.notify(event)

    assert a.events == [event]
    assert b.events == [event]


def test_raises_notification_failed_when_any_child_fails() -> None:
    a = RecordingNotifier()
    b = RecordingNotifier(fail=True)
    notifier = FanOutNotifier([a, b])

    with pytest.raises(NotificationFailed):
        notifier.notify(_event())


def test_all_children_invoked_even_when_one_fails() -> None:
    a = RecordingNotifier(fail=True)
    b = RecordingNotifier()
    notifier = FanOutNotifier([a, b])

    with pytest.raises(NotificationFailed):
        notifier.notify(_event())

    assert a.events != []
    assert b.events != []


def test_empty_children_is_a_no_op() -> None:
    notifier = FanOutNotifier([])

    notifier.notify(_event())  # must not raise
