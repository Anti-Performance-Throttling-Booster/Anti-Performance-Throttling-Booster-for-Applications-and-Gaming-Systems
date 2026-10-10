# monitoring/cpu_monitor.py

import psutil


class CPUMonitor:
    """Collect CPU utilization information."""

    def get_usage(self):
        """Return overall CPU utilization as a percentage."""
        return psutil.cpu_percent(interval=1)

    def get_per_core_usage(self):
        """Return CPU utilization for each logical CPU core."""
        return psutil.cpu_percent(interval=1, percpu=True)

    def get_core_count(self):
        """Return the number of logical CPU cores."""
        return psutil.cpu_count(logical=True)
