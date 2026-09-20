import pytest

gpiod = pytest.importorskip("gpiod")

from gpiod.line import Bias, Direction, Value  # noqa: E402
from gpiod.line_settings import LineSettings  # noqa: E402

from power_monitor.adapters.pin.pin_reader_libgpiod import (  # noqa: E402
    LibGpiodPinReader,
)
from power_monitor.domain.model import PinState  # noqa: E402

pytestmark = pytest.mark.hardware

CHIP = "/dev/gpiochip0"
OFFSET = 17


def test_reads_real_line_without_applying_bias() -> None:
    with gpiod.request_lines(
        CHIP,
        consumer="power-monitor-test",
        config={OFFSET: LineSettings(direction=Direction.INPUT, bias=Bias.DISABLED)},
    ) as request:
        reader = LibGpiodPinReader(request, offset=OFFSET, active=Value.ACTIVE)
        result = reader.read()

    assert isinstance(result, PinState)
