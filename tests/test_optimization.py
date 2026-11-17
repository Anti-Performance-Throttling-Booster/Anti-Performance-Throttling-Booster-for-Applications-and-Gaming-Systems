import pytest

from optimization.optimization_engine import OptimizationEngine
from optimization.profiles import ProfileManager
from optimization.process_analyzer import ProcessAnalyzer


class FakePriorityAdapter:
    def __init__(self, names=None, priorities=None, fail_with=None):
        self.names = names or {101: "Game.exe", 202: "Browser.exe", 303: "svchost.exe"}
        self.priorities = priorities or {101: 0, 202: 0, 303: 0}
        self.fail_with = fail_with
        self.calls = []

    def get_process_name(self, pid):
        return self.names[pid]

    def get_priority(self, pid):
        return self.priorities[pid]

    def set_priority(self, pid, priority_level):
        self.calls.append(("set", pid, priority_level))
        if self.fail_with:
            raise self.fail_with
        self.priorities[pid] = priority_level

    def restore_priority(self, pid, original_priority):
        self.calls.append(("restore", pid, original_priority))
        if self.fail_with:
            raise self.fail_with
        self.priorities[pid] = original_priority


@pytest.fixture
def process_snapshot():
    return [
        {"pid": 101, "name": "Game.exe", "cpu_percent": 1.0, "memory_mb": 900.0},
        {"pid": 202, "name": "Browser.exe", "cpu_percent": 25.0, "memory_mb": 700.0},
        {"pid": 303, "name": "svchost.exe", "cpu_percent": 40.0, "memory_mb": 300.0},
        {"pid": 404, "name": "MemoryTool.exe", "cpu_percent": 1.0, "memory_mb": 4096.0},
    ]


def make_engine(tmp_path, adapter=None):
    manager = ProfileManager(tmp_path / "profiles.json")
    manager.select_profile("Gaming")
    analyzer = ProcessAnalyzer()
    return OptimizationEngine(manager, analyzer, adapter or FakePriorityAdapter())


def test_analyzer_marks_target_and_critical_processes_protected(tmp_path, process_snapshot):
    engine = make_engine(tmp_path)
    rows = engine.get_process_analysis(process_snapshot, target_pid=101)
    by_pid = {row["pid"]: row for row in rows}

    assert by_pid[101]["is_target"] is True
    assert by_pid[303]["is_protected"] is True
    assert by_pid[202]["eligible_for_optimization"] is True
    assert by_pid[404]["memory_heavy"] is True
    assert by_pid[404]["eligible_for_optimization"] is False


def test_no_target_means_no_process_is_eligible(tmp_path, process_snapshot):
    engine = make_engine(tmp_path)
    rows = engine.get_process_analysis(process_snapshot)
    assert not any(row["eligible_for_optimization"] for row in rows)


def test_cancelled_action_does_not_call_adapter(tmp_path, process_snapshot):
    adapter = FakePriorityAdapter()
    engine = make_engine(tmp_path, adapter)
    result = engine.optimize_process(
        202, process_snapshot, confirmed=False, target_pid=101
    )
    assert result["status"] == "cancelled"
    assert adapter.calls == []


def test_successful_action_reports_result(tmp_path, process_snapshot):
    adapter = FakePriorityAdapter()
    engine = make_engine(tmp_path, adapter)
    result = engine.optimize_process(
        202, process_snapshot, confirmed=True, target_pid=101
    )

    assert result["success"] is True
    assert result["status"] == "success"
    assert result["process_name"] == "Browser.exe"
    assert result["action"] == "lower_process_priority"
    assert adapter.calls == [("set", 202, "below_normal")]


def test_protected_process_is_rejected(tmp_path, process_snapshot):
    adapter = FakePriorityAdapter()
    engine = make_engine(tmp_path, adapter)
    result = engine.optimize_process(
        303, process_snapshot, confirmed=True, target_pid=101
    )
    assert result["status"] == "rejected"
    assert adapter.calls == []


def test_memory_only_process_is_not_auto_optimized(tmp_path, process_snapshot):
    adapter = FakePriorityAdapter()
    engine = make_engine(tmp_path, adapter)
    result = engine.optimize_process(
        404, process_snapshot, confirmed=True, target_pid=101
    )
    assert result["status"] == "rejected"
    assert "will not free RAM" in result["message"]
    assert adapter.calls == []


def test_missing_target_is_rejected(tmp_path, process_snapshot):
    adapter = FakePriorityAdapter()
    engine = make_engine(tmp_path, adapter)
    result = engine.optimize_process(
        202, process_snapshot, confirmed=True, target_pid=None
    )
    assert result["status"] == "rejected"
    assert adapter.calls == []


def test_permission_failure_is_reported_safely(tmp_path, process_snapshot):
    adapter = FakePriorityAdapter(fail_with=PermissionError("access denied"))
    engine = make_engine(tmp_path, adapter)
    result = engine.optimize_process(
        202, process_snapshot, confirmed=True, target_pid=101
    )
    assert result["status"] == "failed"
    assert result["success"] is False
    assert "failed safely" in result["message"]


def test_original_priority_can_be_restored(tmp_path, process_snapshot):
    adapter = FakePriorityAdapter()
    engine = make_engine(tmp_path, adapter)
    applied = engine.optimize_process(
        202, process_snapshot, confirmed=True, target_pid=101
    )
    assert applied["success"] is True

    restored = engine.restore_process_priority(202, confirmed=True)
    assert restored["status"] == "restored"
    assert adapter.priorities[202] == 0


def test_profile_action_limit_is_enforced(tmp_path, process_snapshot):
    adapter = FakePriorityAdapter(names={202: "Browser.exe", 505: "Updater.exe"}, priorities={202: 0, 505: 0})
    engine = make_engine(tmp_path, adapter)
    engine.profile_manager.update_profile("Gaming", max_actions=1)

    first = engine.optimize_process(202, process_snapshot, confirmed=True, target_pid=101)
    second_snapshot = process_snapshot + [
        {"pid": 505, "name": "Updater.exe", "cpu_percent": 20.0, "memory_mb": 500.0}
    ]
    second = engine.optimize_process(505, second_snapshot, confirmed=True, target_pid=101)

    assert first["success"] is True
    assert second["status"] == "rejected"
    assert "at most 1" in second["message"]
