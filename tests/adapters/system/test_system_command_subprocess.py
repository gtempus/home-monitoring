import subprocess

import pytest

from power_monitor.adapters.system.system_command_subprocess import (
    SubprocessSystemCommand,
    SystemCommandError,
)


def test_shutdown_invokes_systemctl_poweroff_no_block(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr("subprocess.run", fake_run)

    SubprocessSystemCommand().shutdown()

    assert calls == [["sudo", "systemctl", "--no-block", "poweroff"]]


def test_shutdown_raises_on_nonzero_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr("subprocess.run", fake_run)

    with pytest.raises(SystemCommandError):
        SubprocessSystemCommand().shutdown()


def test_shutdown_raises_on_exec_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        raise FileNotFoundError("systemctl not found")

    monkeypatch.setattr("subprocess.run", fake_run)

    with pytest.raises(SystemCommandError):
        SubprocessSystemCommand().shutdown()
