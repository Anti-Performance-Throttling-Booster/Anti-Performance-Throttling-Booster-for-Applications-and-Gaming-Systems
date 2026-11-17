"""Safe mock-data demo. This never changes a real process's priority."""

from pathlib import Path
from tempfile import TemporaryDirectory
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from optimization.optimization_engine import OptimizationEngine
from optimization.profiles import ProfileManager


sample_processes = [
    {"pid": 1001, "name": "ExampleGame.exe", "cpu_percent": 2.0, "memory_mb": 1800.0},
    {"pid": 1002, "name": "Browser.exe", "cpu_percent": 26.0, "memory_mb": 900.0},
    {"pid": 1003, "name": "svchost.exe", "cpu_percent": 35.0, "memory_mb": 250.0},
]


class DemoAdapter:
    def get_process_name(self, pid):
        return {1001: "ExampleGame.exe", 1002: "Browser.exe", 1003: "svchost.exe"}[pid]

    def get_priority(self, pid):
        return 0

    def set_priority(self, pid, priority_level):
        print(f"[MOCK] PID {pid} priority -> {priority_level}")

    def restore_priority(self, pid, original_priority):
        print(f"[MOCK] PID {pid} priority restored -> {original_priority}")


with TemporaryDirectory() as temp_dir:
    profile_manager = ProfileManager(Path(temp_dir) / "profiles.json")
    profile_manager.select_profile("Gaming")
    engine = OptimizationEngine(
        profile_manager=profile_manager,
        priority_adapter=DemoAdapter(),
    )

    print("Active profile:", profile_manager.active_profile)
    rows = engine.get_process_analysis(sample_processes, target_pid=1001)
    for row in rows:
        print(row)

    result = engine.optimize_process(
        1002,
        sample_processes,
        confirmed=True,  # Simulates a confirmation accepted in the UI.
        target_pid=1001,
    )
    print("Action result:", result)
