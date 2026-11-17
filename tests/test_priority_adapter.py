from types import SimpleNamespace

import pytest

import optimization.priority_adapter as priority_adapter
from optimization.priority_adapter import PsutilPriorityAdapter


class FakeProcess:
    def __init__(self, pid, name="Example.exe", priority=32):
        self.pid = pid
        self._name = name
        self._priority = priority
        self.calls = []

    def name(self):
        return self._name

    def nice(self, *args):
        if not args:
            return self._priority
        self.calls.append(args[0])
        self._priority = args[0]


def install_fake_process(monkeypatch, fake_process):
    requested_pids = []

    def fake_factory(pid):
        requested_pids.append(pid)
        return fake_process

    monkeypatch.setattr(priority_adapter.psutil, "Process", fake_factory)
    return requested_pids


def test_get_process_name_uses_requested_pid(monkeypatch):
    fake = FakeProcess(1234, name="Browser.exe")
    requested_pids = install_fake_process(monkeypatch, fake)

    result = PsutilPriorityAdapter().get_process_name(1234)

    assert result == "Browser.exe"
    assert requested_pids == [1234]


def test_get_priority_returns_original_priority(monkeypatch):
    fake = FakeProcess(1234, priority=32)
    install_fake_process(monkeypatch, fake)

    result = PsutilPriorityAdapter().get_priority(1234)

    assert result == 32


def test_set_priority_uses_windows_below_normal_constant(monkeypatch):
    fake = FakeProcess(1234)
    install_fake_process(monkeypatch, fake)
    monkeypatch.setattr(priority_adapter, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(
        priority_adapter.psutil,
        "BELOW_NORMAL_PRIORITY_CLASS",
        0x4000,
        raising=False,
    )

    PsutilPriorityAdapter().set_priority(1234, "below_normal")

    assert fake.calls == [0x4000]


def test_set_priority_uses_posix_nice_value(monkeypatch):
    fake = FakeProcess(1234)
    install_fake_process(monkeypatch, fake)
    monkeypatch.setattr(priority_adapter, "os", SimpleNamespace(name="posix"))

    PsutilPriorityAdapter().set_priority(1234, "below_normal")

    assert fake.calls == [5]


def test_set_priority_rejects_unsupported_priority(monkeypatch):
    fake = FakeProcess(1234)
    install_fake_process(monkeypatch, fake)

    with pytest.raises(ValueError, match="Unsupported priority level"):
        PsutilPriorityAdapter().set_priority(1234, "high")

    assert fake.calls == []


def test_set_priority_rejects_unsupported_operating_system(monkeypatch):
    fake = FakeProcess(1234)
    install_fake_process(monkeypatch, fake)
    monkeypatch.setattr(priority_adapter, "os", SimpleNamespace(name="unknown"))

    with pytest.raises(OSError, match="unsupported on this OS"):
        PsutilPriorityAdapter().set_priority(1234, "below_normal")

    assert fake.calls == []


def test_restore_priority_sets_original_value(monkeypatch):
    fake = FakeProcess(1234, priority=16384)
    install_fake_process(monkeypatch, fake)

    PsutilPriorityAdapter().restore_priority(1234, 32)

    assert fake.calls == [32]
    assert fake._priority == 32
