from power_monitor.domain.ports.system_command import SystemCommand


class LogOnlySystemCommand(SystemCommand):
    """TEMP: logs intent but does not shut down.

    Replace with a real SystemCommand adapter before the timer is
    trusted to actually power off the Pi. See `# TEMP` marker in
    entrypoints/cron.py.
    """

    def shutdown(self) -> None:
        print("SYSTEM_COMMAND: would shut down now (dry-run)", flush=True)