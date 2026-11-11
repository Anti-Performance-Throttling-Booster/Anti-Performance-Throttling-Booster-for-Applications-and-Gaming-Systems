# monitoring/process_monitor.py

import psutil


class ProcessMonitor:
    """Collect resource usage information for running processes."""

    def get_all_processes(self):
        """Return resource usage information for accessible processes."""
        processes = []

        for process in psutil.process_iter(
            attrs=["pid", "name", "memory_info"]
        ):
            try:
                info = process.info
                memory_info = info["memory_info"]

                processes.append({
                    "pid": info["pid"],
                    "name": info["name"] or "Unknown",
                    "cpu_percent": process.cpu_percent(interval=None),
                    "memory_mb": round(
                        memory_info.rss / (1024 ** 2), 2
                    ) if memory_info else 0.0,
                })

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess,
            ):
                # Skip processes that disappear or cannot be accessed.
                continue

        return processes

    def get_top_cpu_processes(self, limit=10):
        """Return processes sorted by CPU utilization."""
        processes = self.get_all_processes()

        processes.sort(
            key=lambda process: process["cpu_percent"],
            reverse=True,
        )

        return processes[:limit]

    def get_top_memory_processes(self, limit=10):
        """Return processes sorted by memory consumption."""
        processes = self.get_all_processes()

        processes.sort(
            key=lambda process: process["memory_mb"],
            reverse=True,
        )

        return processes[:limit]
