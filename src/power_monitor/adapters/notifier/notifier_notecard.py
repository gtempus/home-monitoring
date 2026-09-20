import time
from typing import Protocol

from power_monitor.domain.errors import NotificationFailed
from power_monitor.domain.events import (
    Event,
    FirstRunEvent,
    HeartbeatEvent,
    PowerEvent,
)
from power_monitor.domain.ports.notifier import Notifier


class NotecardLike(Protocol):
    def Transaction(self, req: dict[str, object]) -> dict[str, object]: ...


class NotecardNotifier(Notifier):
    def __init__(
        self,
        card: NotecardLike,
        notefile: str,
        initial_delay: float = 5.0,
        poll_interval: float = 3.0,
        sync_timeout: float = 120.0,
    ) -> None:
        self._card = card
        self._notefile = notefile
        self._initial_delay = initial_delay
        self._poll_interval = poll_interval
        self._sync_timeout = sync_timeout

    def notify(self, event: Event) -> None:
        body = self._serialize(event)  # outside try — serialization bugs propagate
        req: dict[str, object] = {
            "req": "note.add",
            "file": self._notefile,
            "body": body,
            "sync": True,
        }
        try:
            self._card.Transaction(req)
            self._wait_for_sync()
        except NotificationFailed:
            raise
        except Exception as exc:
            raise NotificationFailed(f"notecard transaction failed: {exc}") from exc

    def _wait_for_sync(self) -> None:
        time.sleep(self._initial_delay)
        deadline = time.monotonic() + self._sync_timeout
        while True:
            rsp = self._card.Transaction({"req": "hub.sync.status"})
            if "err" in rsp:
                raise NotificationFailed(f"hub.sync.status error: {rsp['err']}")
            if not rsp.get("sync", False):
                return
            if time.monotonic() >= deadline:
                raise NotificationFailed("sync did not complete within timeout")
            time.sleep(self._poll_interval)

    def _serialize(self, event: Event) -> dict[str, object]:
        if isinstance(event, PowerEvent):
            return {
                "event": "power",
                "state": event.state.name,
                "timestamp": event.at.value.isoformat(),
            }
        if isinstance(event, HeartbeatEvent):
            return {
                "event": "heartbeat",
                "timestamp": event.at.value.isoformat(),
            }
        if isinstance(event, FirstRunEvent):
            return {
                "event": "first_run",
                "state": event.power_state.name,
                "timestamp": event.at.value.isoformat(),
            }
        raise AssertionError(f"unhandled event type: {type(event).__name__}")
