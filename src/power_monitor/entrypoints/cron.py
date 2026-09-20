from pathlib import Path

import gpiod
import notecard
import serial
from gpiod.line import Bias, Direction, Value
from gpiod.line_settings import LineSettings

from power_monitor.adapters.clock.system_clock import SystemClock
from power_monitor.adapters.notifier.log_notifier import LogNotifier
from power_monitor.adapters.notifier.notifier_fanout import FanOutNotifier
from power_monitor.adapters.notifier.notifier_notecard import NotecardNotifier
from power_monitor.adapters.pin.power_state_reader_libgpiod import (
    LibGpiodPowerStateReader,
)
from power_monitor.adapters.state.state_repository_json import JsonStateRepository
from power_monitor.adapters.system.log_only_system_command import (
    LogOnlySystemCommand,  # TEMP
)
from power_monitor.domain.check_power import CheckPower

CHIP_PATH = "/dev/gpiochip0"
PIN_OFFSET = 23  # hardware signal pin: LOW voltage = power ON
ON_VALUE = Value.INACTIVE  # LOW voltage = power ON, per the monitored hardware
STATE_PATH = Path("/var/lib/power-monitor/state.json")
CONSUMER = "power-monitor"
SERIAL_PORT = "/dev/serial0"
SERIAL_BAUD = 9600
NOTEFILE = "data.qo"


def main() -> None:
    repo = JsonStateRepository(STATE_PATH)
    port = serial.Serial(SERIAL_PORT, SERIAL_BAUD)
    card = notecard.OpenSerial(port)
    notifier = FanOutNotifier(
        [
            LogNotifier(),
            NotecardNotifier(card, notefile=NOTEFILE),
        ]
    )
    system = LogOnlySystemCommand()  # TEMP: replace with real adapter

    with gpiod.request_lines(
        CHIP_PATH,
        consumer=CONSUMER,
        config={PIN_OFFSET: LineSettings(direction=Direction.INPUT, bias=Bias.DISABLED)},
    ) as request:
        reader = LibGpiodPowerStateReader(request, offset=PIN_OFFSET, on_value=ON_VALUE)
        CheckPower(SystemClock(), reader, repo, notifier, system).run()


if __name__ == "__main__":
    main()
