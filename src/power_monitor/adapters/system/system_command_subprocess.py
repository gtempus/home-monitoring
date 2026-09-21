import subprocess

from power_monitor.domain.ports.system_command import SystemCommand

COMMAND = ["sudo", "systemctl", "--no-block", "poweroff"]


class SystemCommandError(Exception):
    """Raised when the shutdown command cannot be issued."""


class SubprocessSystemCommand(SystemCommand):
    def shutdown(self) -> None:
        try:
            subprocess.run(COMMAND, check=True, capture_output=True)
        except (subprocess.CalledProcessError, OSError) as exc:
            raise SystemCommandError(f"failed to issue shutdown: {exc}") from exc
