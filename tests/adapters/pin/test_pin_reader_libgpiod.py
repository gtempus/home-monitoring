import pytest

from power_monitor.adapters.pin.pin_reader_libgpiod import (
    LibGpiodPinReader,
    PinReaderError,
)
from power_monitor.domain.model import PinState

ACTIVE = 1
INACTIVE = 0


class FakeLineRequest:
    def __init__(self, value: object = 0, error: Exception | None = None) -> None:
        self._value = value
        self._error = error

    def get_value(self, offset: int) -> object:
        if self._error is not None:
            raise self._error
        return self._value


def test_read_returns_high_when_value_is_active() -> None:
    reader = LibGpiodPinReader(FakeLineRequest(value=ACTIVE), offset=17, active=ACTIVE)
    assert reader.read() is PinState.HIGH


def test_read_returns_low_when_value_is_inactive() -> None:
    reader = LibGpiodPinReader(FakeLineRequest(value=INACTIVE), offset=17, active=ACTIVE)
    assert reader.read() is PinState.LOW


def test_read_raises_pin_reader_error_on_io_failure() -> None:
    reader = LibGpiodPinReader(
        FakeLineRequest(error=OSError("gpio busy")), offset=17, active=ACTIVE
    )
    with pytest.raises(PinReaderError):
        reader.read()
