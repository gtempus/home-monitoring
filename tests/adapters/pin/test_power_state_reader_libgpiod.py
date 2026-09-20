import pytest

from power_monitor.adapters.pin.power_state_reader_libgpiod import (
    LibGpiodPowerStateReader,
    PowerStateReaderError,
)
from power_monitor.domain.model import PowerState

ON = 1
OFF = 0


class FakeLineRequest:
    def __init__(self, value: object = 0, error: Exception | None = None) -> None:
        self._value = value
        self._error = error

    def get_value(self, offset: int) -> object:
        if self._error is not None:
            raise self._error
        return self._value


def test_read_returns_on_when_value_matches_on_value() -> None:
    reader = LibGpiodPowerStateReader(FakeLineRequest(value=ON), offset=17, on_value=ON)
    assert reader.read() is PowerState.ON


def test_read_returns_off_when_value_does_not_match_on_value() -> None:
    reader = LibGpiodPowerStateReader(FakeLineRequest(value=OFF), offset=17, on_value=ON)
    assert reader.read() is PowerState.OFF


def test_read_raises_power_state_reader_error_on_io_failure() -> None:
    reader = LibGpiodPowerStateReader(
        FakeLineRequest(error=OSError("gpio busy")), offset=17, on_value=ON
    )
    with pytest.raises(PowerStateReaderError):
        reader.read()
