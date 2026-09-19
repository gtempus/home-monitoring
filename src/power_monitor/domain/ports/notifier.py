from typing import Protocol

from power_monitor.domain.events import Event


class Notifier(Protocol):
    def notify(self, event: Event) -> None: ...