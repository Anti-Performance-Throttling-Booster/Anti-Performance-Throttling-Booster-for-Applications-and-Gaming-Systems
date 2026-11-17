"""Analyze process snapshots supplied by Member 1's monitoring module."""

from __future__ import annotations

import os
from typing import Iterable

from optimization.profiles import PerformanceProfile


# Conservative Windows/system-process deny list. This is an additional safeguard,
# not a complete substitute for OS-level protection or user confirmation.
PROTECTED_PROCESS_NAMES = frozenset(
    {
        "system",
        "system idle process",
        "registry",
        "smss.exe",
        "csrss.exe",
        "wininit.exe",
        "services.exe",
        "lsass.exe",
        "svchost.exe",
        "winlogon.exe",
        "dwm.exe",
        "fontdrvhost.exe",
        "explorer.exe",
        "sihost.exe",
        "taskhostw.exe",
        "audiodg.exe",
        "securityhealthservice.exe",
        "msmpeng.exe",
    }
)


class ProcessAnalyzer:
    """Rank resource-heavy processes and mark safe candidates for review."""

    def __init__(self, protected_process_names: Iterable[str] | None = None) -> None:
        names = protected_process_names or PROTECTED_PROCESS_NAMES
        self.protected_process_names = {name.casefold() for name in names}

    def analyze(
        self,
        processes: list[dict],
        profile: PerformanceProfile,
        *,
        target_pid: int | None = None,
        protected_pids: Iterable[int] | None = None,
    ) -> list[dict]:
        """Return process rows with resource flags and optimization eligibility.

        The Member 1 snapshot contains metrics but does not identify window focus.
        Therefore, results are described as *potential background candidates*.
        The user-selected target application is always excluded from optimization.
        """
        if not isinstance(processes, list):
            raise TypeError("Process snapshot must be a list.")

        protected_pid_set = set(protected_pids or [])
        protected_pid_set.add(os.getpid())
        analyzed: list[dict] = []

        for raw in processes:
            if not isinstance(raw, dict):
                continue

            pid = raw.get("pid")
            name = raw.get("name")
            if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
                continue
            if not isinstance(name, str) or not name.strip():
                continue

            cpu_percent = self._safe_non_negative_number(raw.get("cpu_percent"))
            memory_mb = self._safe_non_negative_number(raw.get("memory_mb"))
            if cpu_percent is None or memory_mb is None:
                continue

            normalized_name = name.strip().casefold()
            is_target = target_pid is not None and pid == target_pid
            is_protected = (
                pid in protected_pid_set
                or pid <= 4
                or normalized_name in self.protected_process_names
            )
            cpu_heavy = cpu_percent >= profile.cpu_threshold_percent
            memory_heavy = memory_mb >= profile.memory_threshold_mb
            resource_intensive = cpu_heavy or memory_heavy

            eligible = (
                target_pid is not None
                and resource_intensive
                and cpu_heavy
                and not is_protected
                and not is_target
            )

            if is_target:
                recommendation = "Protected: this is the selected application/game."
            elif is_protected:
                recommendation = "Protected system or user-protected process; no action is permitted."
            elif not resource_intensive:
                recommendation = "Below the active profile's resource thresholds."
            elif memory_heavy and not cpu_heavy:
                recommendation = (
                    "High memory use. Lowering CPU priority will not free RAM; "
                    "review this process manually."
                )
            elif target_pid is None:
                recommendation = (
                    "Potential resource-heavy background process. Select the target "
                    "application/game before optimization can be enabled."
                )
            else:
                recommendation = (
                    "Potential background candidate: high CPU use. A confirmed "
                    "priority reduction may reduce competition with the target workload."
                )

            analyzed.append(
                {
                    "pid": pid,
                    "name": name.strip(),
                    "cpu_percent": cpu_percent,
                    "memory_mb": memory_mb,
                    "cpu_heavy": cpu_heavy,
                    "memory_heavy": memory_heavy,
                    "resource_intensive": resource_intensive,
                    "is_target": is_target,
                    "is_protected": is_protected,
                    "potential_background_candidate": resource_intensive and not is_target and not is_protected,
                    "eligible_for_optimization": eligible,
                    "recommendation": recommendation,
                }
            )

        return sorted(
            analyzed,
            key=lambda item: (item["cpu_percent"], item["memory_mb"]),
            reverse=True,
        )

    @staticmethod
    def _safe_non_negative_number(value: object) -> float | None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        number = float(value)
        if number < 0:
            return None
        return number
