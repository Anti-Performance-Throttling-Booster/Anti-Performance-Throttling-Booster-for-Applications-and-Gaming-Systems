"""Operating-system-specific process-priority operations."""

from __future__ import annotations

import os
import psutil


class PsutilPriorityAdapter:
    """Small adapter isolating psutil and OS-specific priority constants."""

    def get_process_name(self, pid: int) -> str:
        return psutil.Process(pid).name()

    def get_priority(self, pid: int):
        return psutil.Process(pid).nice()

    def set_priority(self, pid: int, priority_level: str) -> None:
        if priority_level != "below_normal":
            raise ValueError(f"Unsupported priority level: {priority_level}")

        if os.name == "nt":
            target_priority = psutil.BELOW_NORMAL_PRIORITY_CLASS
        elif os.name == "posix":
            # A larger nice value gives the process a lower scheduling priority.
            target_priority = 5
        else:
            raise OSError("Process-priority optimization is unsupported on this OS.")

        psutil.Process(pid).nice(target_priority)

    def restore_priority(self, pid: int, original_priority) -> None:
        psutil.Process(pid).nice(original_priority)
