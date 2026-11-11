# monitoring/engine.py

import threading
import time

from monitoring.cpu_monitor import CPUMonitor
from monitoring.memory_monitor import MemoryMonitor
from monitoring.process_monitor import ProcessMonitor


class MonitoringEngine:
    """Coordinate CPU, memory, and process monitoring."""

    def __init__(self, refresh_interval=1.0):
        if refresh_interval <= 0:
            raise ValueError("Refresh interval must be greater than zero.")

        self.refresh_interval = refresh_interval

        self.cpu_monitor = CPUMonitor()
        self.memory_monitor = MemoryMonitor()
        self.process_monitor = ProcessMonitor()

        self._latest_metrics = None
        self._running = False
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._thread = None

    @property
    def is_running(self):
        """Return whether the monitoring engine is running."""
        with self._lock:
            return self._running

    def start(self):
        """Start periodic metric collection in a background thread."""
        with self._lock:
            if self._running:
                return

            self._stop_event.clear()
            self._running = True

            self._thread = threading.Thread(
                target=self._monitor_loop,
                name="monitoring-engine",
                daemon=True,
            )
            self._thread.start()

    def stop(self):
        """Stop periodic metric collection."""
        with self._lock:
            thread = self._thread

            if thread is None:
                return

            self._stop_event.set()

        if thread is not threading.current_thread():
            thread.join()

        with self._lock:
            self._running = False
            self._thread = None

    def get_metrics(self):
        """Return the latest collected metrics."""
        with self._lock:
            if self._latest_metrics is None:
                return None

            return {
                "timestamp": self._latest_metrics["timestamp"],
                "cpu": dict(self._latest_metrics["cpu"]),
                "memory": dict(self._latest_metrics["memory"]),
                "processes": [
                    dict(process)
                    for process in self._latest_metrics["processes"]
                ],
            }

    def _collect_metrics(self):
        """Collect one snapshot of system metrics."""
        from datetime import datetime

        return {
            "timestamp": datetime.now().astimezone().isoformat(
                timespec="seconds"
            ),
            "cpu": {
                "usage_percent": self.cpu_monitor.get_usage(),
                "logical_cores": self.cpu_monitor.get_core_count(),
            },
            "memory": self.memory_monitor.get_memory_details(),
            "processes": self.process_monitor.get_all_processes(),
        }

    def _monitor_loop(self):
        """Collect metrics repeatedly until monitoring is stopped."""
        while not self._stop_event.is_set():
            try:
                metrics = self._collect_metrics()

                with self._lock:
                    self._latest_metrics = metrics

            except Exception as error:
                # Keep the engine alive if one collection cycle fails.
                print(f"Monitoring error: {error}")

            # Wait interruptibly, so Stop can end the waiting period.
            self._stop_event.wait(self.refresh_interval)

        with self._lock:
            self._running = False
