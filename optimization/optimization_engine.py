"""User-confirmed, fail-safe process-priority optimization."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

import psutil

from optimization.process_analyzer import ProcessAnalyzer
from optimization.profiles import ProfileManager
from optimization.priority_adapter import PsutilPriorityAdapter


class OptimizationEngine:
    """Apply only a permitted priority change after explicit user confirmation.

    This module deliberately does not terminate, kill, suspend, or close processes.
    """

    def __init__(
        self,
        profile_manager: ProfileManager | None = None,
        process_analyzer: ProcessAnalyzer | None = None,
        priority_adapter: PsutilPriorityAdapter | None = None,
    ) -> None:
        self.profile_manager = profile_manager or ProfileManager()
        self.process_analyzer = process_analyzer or ProcessAnalyzer()
        self.priority_adapter = priority_adapter or PsutilPriorityAdapter()
        self._original_priorities: dict[int, tuple[str, object]] = {}
        self._optimized_pids_by_profile: dict[str, set[int]] = {}

    def get_process_analysis(
        self,
        processes: list[dict],
        *,
        target_pid: int | None = None,
        protected_pids: Iterable[int] | None = None,
    ) -> list[dict]:
        """Analyze the latest Member 1 process snapshot using the active profile."""
        return self.process_analyzer.analyze(
            processes,
            self.profile_manager.active_profile,
            target_pid=target_pid,
            protected_pids=protected_pids,
        )

    def optimize_process(
        self,
        pid: int,
        processes: list[dict],
        *,
        confirmed: bool,
        target_pid: int | None,
        protected_pids: Iterable[int] | None = None,
    ) -> dict:
        """Lower an eligible process's priority and return a reportable result.

        `confirmed` must be True only after the UI has shown the process name,
        PID, action, and profile and the user has accepted the confirmation dialog.
        `target_pid` is mandatory so the user's selected application/game is protected.
        """
        profile = self.profile_manager.active_profile
        timestamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

        if confirmed is not True:
            return self._result(
                timestamp, pid, None, profile.name, "cancelled",
                "No change was made because user confirmation was not received.",
            )

        if target_pid is None:
            return self._result(
                timestamp, pid, None, profile.name, "rejected",
                "Select the target application/game before optimizing other processes.",
            )

        if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
            return self._result(
                timestamp, pid, None, profile.name, "rejected",
                "Invalid process ID.",
            )

        analyzed = self.get_process_analysis(
            processes,
            target_pid=target_pid,
            protected_pids=protected_pids,
        )
        candidate = next((item for item in analyzed if item["pid"] == pid), None)
        if candidate is None:
            return self._result(
                timestamp, pid, None, profile.name, "rejected",
                "The process is missing from the latest process snapshot. Refresh the list and try again.",
            )
        if not candidate["eligible_for_optimization"]:
            return self._result(
                timestamp, pid, candidate["name"], profile.name, "rejected",
                candidate["recommendation"],
            )

        optimized_pids = self._optimized_pids_by_profile.setdefault(profile.name, set())
        if pid not in optimized_pids and len(optimized_pids) >= profile.max_actions:
            return self._result(
                timestamp, pid, candidate["name"], profile.name, "rejected",
                f"The active profile allows at most {profile.max_actions} priority changes in this session.",
            )

        try:
            actual_name = self.priority_adapter.get_process_name(pid)
            if actual_name.casefold() != candidate["name"].casefold():
                return self._result(
                    timestamp, pid, candidate["name"], profile.name, "rejected",
                    "The process changed since the list was loaded. Refresh the process list before retrying.",
                )

            original_priority = self.priority_adapter.get_priority(pid)
            self.priority_adapter.set_priority(pid, profile.priority_target)
            self._original_priorities.setdefault(pid, (actual_name, original_priority))
            optimized_pids.add(pid)

            return self._result(
                timestamp,
                pid,
                actual_name,
                profile.name,
                "success",
                f"Priority was changed to below-normal for {actual_name}.",
            )
        except psutil.NoSuchProcess:
            message = "The process no longer exists. No optimization was completed."
        except psutil.AccessDenied:
            message = "The operating system denied permission. Run with appropriate permissions or leave the process unchanged."
        except psutil.ZombieProcess:
            message = "The process is no longer active. No optimization was completed."
        except (OSError, PermissionError, ValueError) as error:
            message = f"Optimization failed safely: {error}"
        except psutil.Error:
            message = "The operating system process API reported an error. No optimization was completed."

        return self._result(
            timestamp, pid, candidate["name"], profile.name, "failed", message,
        )

    def restore_process_priority(self, pid: int, *, confirmed: bool) -> dict:
        """Restore the original priority of a process changed by this engine."""
        timestamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        profile_name = self.profile_manager.active_profile.name

        if confirmed is not True:
            return self._result(
                timestamp, pid, None, profile_name, "cancelled",
                "Priority was not restored because confirmation was not received.",
            )

        original = self._original_priorities.get(pid)
        if original is None:
            return self._result(
                timestamp, pid, None, profile_name, "rejected",
                "This session has no saved original priority for that process.",
            )

        expected_name, original_priority = original
        try:
            actual_name = self.priority_adapter.get_process_name(pid)
            if actual_name.casefold() != expected_name.casefold():
                return self._result(
                    timestamp, pid, expected_name, profile_name, "rejected",
                    "The process ID now belongs to a different process. Priority was not restored.",
                )
            self.priority_adapter.restore_priority(pid, original_priority)
            del self._original_priorities[pid]
            for changed_pids in self._optimized_pids_by_profile.values():
                changed_pids.discard(pid)
            return self._result(
                timestamp, pid, actual_name, profile_name, "restored",
                f"Original priority restored for {actual_name}.",
            )
        except psutil.ZombieProcess:
            message = "The process is no longer active. No optimization was completed."
        except psutil.NoSuchProcess:
            message = "The process no longer exists. No optimization was completed."
        except psutil.AccessDenied:
            message = "The operating system denied permission. Run with appropriate permissions or leave the process unchanged."

        return self._result(
            timestamp, pid, expected_name, profile_name, "failed", message,
        )

    @staticmethod
    def _result(
        timestamp: str,
        pid: int,
        process_name: str | None,
        profile_name: str,
        status: str,
        message: str,
    ) -> dict:
        """Return a stable result structure for the UI and Member 4's logger."""
        return {
            "timestamp": timestamp,
            "pid": pid,
            "process_name": process_name,
            "profile_name": profile_name,
            "action": "lower_process_priority",
            "status": status,
            "success": status in {"success", "restored"},
            "message": message,
        }
