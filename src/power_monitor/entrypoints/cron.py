from pathlib import Path

import gpiod
from gpiod.line import Bias, Direction, Value
from gpiod.line_settings import LineSettings

from power_monitor.adapters.clock.system_clock import SystemClock
from power_monitor.adapters.notifier.log_notifier import LogNotifier
from power_monitor.adapters.pin.pin_reader_libgpiod import LibGpiodPinReader
from power_monitor.adapters.state.state_repository_json import JsonStateRepository
from power_monitor.adapters.system.log_only_system_command import (
    LogOnlySystemCommand,  # TEMP
)
from power_monitor.domain.check_power import CheckPower

CHIP_PATH = "/dev/gpiochip0"
PIN_OFFSET = 17
STATE_PATH = Path("/var/lib/power-monitor/state.json")
CONSUMER = "power-monitor"


def main() -> None:
    repo = JsonStateRepository(STATE_PATH)
    notifier = LogNotifier()
    system = LogOnlySystemCommand()  # TEMP: replace with real adapter

    with gpiod.request_lines(
            CHIP_PATH,
            consumer=CONSUMER,
            config={
                PIN_OFFSET: LineSettings(
                    direction=Direction.INPUT, bias=Bias.DISABLED
                )
            },
    ) as request:
        pin = LibGpiodPinReader(request, offset=PIN_OFFSET, active=Value.ACTIVE)
        CheckPower(SystemClock(), pin, repo, notifier, system).run()


if __name__ == "__main__":
    main()