from typing import Protocol


class SystemCommand(Protocol):
    def shutdown(self) -> None: ...