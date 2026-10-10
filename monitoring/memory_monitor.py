# monitoring/memory_monitor.py

import psutil


class MemoryMonitor:
    """Collect system memory utilization information."""

    def get_memory_usage(self):
        """Return memory utilization as a percentage."""
        return psutil.virtual_memory().percent

    def get_total_memory(self):
        """Return total physical memory in bytes."""
        return psutil.virtual_memory().total

    def get_used_memory(self):
        """Return used physical memory in bytes."""
        return psutil.virtual_memory().used

    def get_available_memory(self):
        """Return available physical memory in bytes."""
        return psutil.virtual_memory().available

    def get_memory_details(self):
        """Return all essential memory metrics in one dictionary."""
        memory = psutil.virtual_memory()

        return {
            "usage_percent": memory.percent,
            "total_mb": round(memory.total / (1024 ** 2), 2),
            "used_mb": round(memory.used / (1024 ** 2), 2),
            "available_mb": round(memory.available / (1024 ** 2), 2),
        }
