from power_monitor.domain.events import Event
from power_monitor.domain.ports.notifier import Notifier


class LogNotifier(Notifier):
    """Writes events to stdout; systemd routes stdout to journalctl."""

    def notify(self, event: Event) -> None:
        print(f"NOTIFY: {event!r}", flush=True)