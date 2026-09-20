from datetime import UTC, datetime

from power_monitor.domain.ports.clock import Clock


class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now(UTC)