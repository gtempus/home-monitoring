import pytest

gpiod = pytest.importorskip("gpiod")

from gpiod.line import Bias, Direction, Value  # noqa: E402
from gpiod.line_settings import LineSettings  # noqa: E402

from power_monitor.adapters.pin.power_state_reader_libgpiod import (  # noqa: E402
    LibGpiodPowerStateReader,
)
from power_monitor.domain.model import PowerState  # noqa: E402

pytestmark = pytest.mark.hardware

CHIP = "/dev/gpiochip0"
OFFSET = 23


def test_reads_real_line_without_applying_bias() -> None:
    with gpiod.request_lines(
        CHIP,
        consumer="power-monitor-test",
        config={OFFSET: LineSettings(direction=Direction.INPUT, bias=Bias.DISABLED)},
    ) as request:
        reader = LibGpiodPowerStateReader(request, offset=OFFSET, on_value=Value.INACTIVE)
        result = reader.read()

    assert isinstance(result, PowerState)
