from datetime import UTC, datetime

import pytest

from power_monitor.adapters.notifier.notifier_notecard import NotecardNotifier
from power_monitor.domain.errors import NotificationFailed
from power_monitor.domain.events import (
    FirstRunEvent,
    HeartbeatEvent,
    PowerEvent,
)
from power_monitor.domain.model import PowerState, Timestamp

NOTEFILE = "power.qo"


class FakeNotecard:
    """Returns queued responses in order; falls back to {total: 1}."""

    def __init__(
        self,
        responses: list[object] | None = None,
    ) -> None:
        self.transactions: list[dict[str, object]] = []
        self._responses: list[object] = list(responses or [])
        self._index = 0

    def Transaction(self, req: dict[str, object]) -> dict[str, object]:
        self.transactions.append(req)
        if self._index < len(self._responses):
            rsp = self._responses[self._index]
            self._index += 1
            if isinstance(rsp, Exception):
                raise rsp
            return rsp  # type: ignore[return-value]
        return {"total": 1}


def _notifier(card: FakeNotecard) -> NotecardNotifier:
    return NotecardNotifier(
        card,
        notefile=NOTEFILE,
        initial_delay=0.0,
        poll_interval=0.0,
        sync_timeout=1.0,
    )


def test_power_event_off_queues_note_and_waits_for_sync() -> None:
    card = FakeNotecard(
        responses=[
            {"total": 1},  # note.add
            {"sync": True, "requested": 1},  # hub.sync.status (in flight)
            {"sync": False, "completed": 1},  # hub.sync.status (done)
        ]
    )
    notifier = _notifier(card)
    at = Timestamp(datetime(2026, 9, 20, 20, 40, 1, tzinfo=UTC))

    notifier.notify(PowerEvent(PowerState.OFF, at))

    assert card.transactions == [
        {
            "req": "note.add",
            "file": NOTEFILE,
            "body": {
                "event": "power",
                "state": "OFF",
                "timestamp": "2026-09-20T20:40:01+00:00",
            },
            "sync": True,
        },
        {"req": "hub.sync.status"},
        {"req": "hub.sync.status"},
    ]


def test_power_event_on_queues_note() -> None:
    card = FakeNotecard(responses=[{"total": 1}, {"sync": False}])
    notifier = _notifier(card)
    at = Timestamp(datetime(2026, 9, 20, 20, 35, 1, tzinfo=UTC))

    notifier.notify(PowerEvent(PowerState.ON, at))

    assert card.transactions[0]["body"] == {
        "event": "power",
        "state": "ON",
        "timestamp": "2026-09-20T20:35:01+00:00",
    }


def test_heartbeat_event_queues_note_without_state() -> None:
    card = FakeNotecard(responses=[{"total": 1}, {"sync": False}])
    notifier = _notifier(card)
    at = Timestamp(datetime(2026, 10, 1, 12, 0, 0, tzinfo=UTC))

    notifier.notify(HeartbeatEvent(at))

    assert card.transactions[0]["body"] == {
        "event": "heartbeat",
        "timestamp": "2026-10-01T12:00:00+00:00",
    }


def test_first_run_event_queues_note_with_state() -> None:
    card = FakeNotecard(responses=[{"total": 1}, {"sync": False}])
    notifier = _notifier(card)
    at = Timestamp(datetime(2026, 9, 20, 20, 35, 1, tzinfo=UTC))

    notifier.notify(FirstRunEvent(PowerState.ON, at))

    assert card.transactions[0]["body"] == {
        "event": "first_run",
        "state": "ON",
        "timestamp": "2026-09-20T20:35:01+00:00",
    }


def test_note_add_failure_raises_notification_failed() -> None:
    card = FakeNotecard(responses=[Exception("notecard busy")])
    notifier = _notifier(card)
    at = Timestamp(datetime(2026, 9, 20, 20, 40, 1, tzinfo=UTC))

    with pytest.raises(NotificationFailed):
        notifier.notify(PowerEvent(PowerState.OFF, at))


def test_hub_sync_status_error_raises_notification_failed() -> None:
    card = FakeNotecard(
        responses=[
            {"total": 1},
            {"err": "notecard busy"},
        ]
    )
    notifier = _notifier(card)
    at = Timestamp(datetime(2026, 9, 20, 20, 40, 1, tzinfo=UTC))

    with pytest.raises(NotificationFailed):
        notifier.notify(PowerEvent(PowerState.OFF, at))


def test_sync_never_completes_raises_notification_failed() -> None:
    card = FakeNotecard(
        responses=[
            {"total": 1},
            {"sync": True},  # always in flight
        ]
    )
    notifier = NotecardNotifier(
        card,
        notefile=NOTEFILE,
        initial_delay=0.0,
        poll_interval=0.0,
        sync_timeout=0.0,  # fail on first check
    )
    at = Timestamp(datetime(2026, 9, 20, 20, 40, 1, tzinfo=UTC))

    with pytest.raises(NotificationFailed):
        notifier.notify(PowerEvent(PowerState.OFF, at))


def test_sync_completes_on_first_poll() -> None:
    card = FakeNotecard(
        responses=[
            {"total": 1},
            {"sync": False},  # already done
        ]
    )
    notifier = _notifier(card)
    at = Timestamp(datetime(2026, 9, 20, 20, 40, 1, tzinfo=UTC))

    notifier.notify(PowerEvent(PowerState.OFF, at))

    # Only note.add + one hub.sync.status
    assert len(card.transactions) == 2
    assert card.transactions[1] == {"req": "hub.sync.status"}
