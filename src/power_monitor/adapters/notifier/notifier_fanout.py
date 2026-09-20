from collections.abc import Sequence

from power_monitor.domain.errors import NotificationFailed
from power_monitor.domain.events import Event
from power_monitor.domain.ports.notifier import Notifier


class FanOutNotifier(Notifier):
    def __init__(self, children: Sequence[Notifier]) -> None:
        self._children = children

    def notify(self, event: Event) -> None:
        failures: list[NotificationFailed] = []
        for child in self._children:
            try:
                child.notify(event)
            except NotificationFailed as exc:
                failures.append(exc)
        if failures:
            raise NotificationFailed(
                f"{len(failures)} of {len(self._children)} notifiers failed"
            ) from failures[0]
