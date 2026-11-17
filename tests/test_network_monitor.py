
import pytest

from monitoring.network_monitor import NetworkMonitor


class FakeCounters:
    def __init__(self, sent, received):
        self.bytes_sent = sent
        self.bytes_recv = received


def setup_monitor(monkeypatch, sent=1000, received=2000):
    current = {"sent": sent, "received": received}
    clock = {"time": 100.0}

    def fake_counters(pernic=False):
        return FakeCounters(
            current["sent"],
            current["received"]
        )

    monkeypatch.setattr(
        "monitoring.network_monitor.psutil.net_io_counters",
        fake_counters
    )

    monkeypatch.setattr(
        "monitoring.network_monitor.time.monotonic",
        lambda: clock["time"]
    )

    return current, clock


def test_monitor_starts_successfully(monkeypatch):
    setup_monitor(monkeypatch)

    monitor = NetworkMonitor()
    result = monitor.start_monitoring()

    assert result["status"] == "started"
    assert monitor.is_monitoring is True
    assert monitor.start_time is not None


def test_download_and_upload_speed(monkeypatch):
    current, clock = setup_monitor(monkeypatch)

    monitor = NetworkMonitor()
    monitor.start_monitoring()

    current["sent"] += 5000
    current["received"] += 10000
    clock["time"] += 2

    stats = monitor.get_network_stats()

    assert stats["upload_speed_bytes_per_second"] == 2500
    assert stats["download_speed_bytes_per_second"] == 5000


def test_total_transferred_data(monkeypatch):
    current, clock = setup_monitor(monkeypatch)

    monitor = NetworkMonitor()
    monitor.start_monitoring()

    current["sent"] += 4000
    current["received"] += 8000
    clock["time"] += 2

    stats = monitor.get_network_stats()

    assert stats["total_uploaded_bytes"] == 4000
    assert stats["total_downloaded_bytes"] == 8000


def test_monitoring_period_tracking(monkeypatch):
    current, clock = setup_monitor(monkeypatch)

    monitor = NetworkMonitor()
    monitor.start_monitoring()

    current["sent"] += 1000
    current["received"] += 2000
    clock["time"] += 5

    monitor.get_network_stats()

    session = monitor.get_session_stats()

    assert session["start_time"] is not None
    assert session["duration_seconds"] == 5
    assert session["is_monitoring"] is True


def test_download_threshold_alert(monkeypatch):
    current, clock = setup_monitor(monkeypatch)

    monitor = NetworkMonitor(
        download_threshold=1000,
        alert_cooldown=30
    )
    monitor.start_monitoring()

    current["received"] += 5000
    clock["time"] += 1

    stats = monitor.get_network_stats()

    assert len(stats["alerts"]) == 1
    assert (
        stats["alerts"][0]["event_type"]
        == "DOWNLOAD_THRESHOLD_EXCEEDED"
    )


def test_upload_threshold_alert(monkeypatch):
    current, clock = setup_monitor(monkeypatch)

    monitor = NetworkMonitor(
        upload_threshold=1000
    )
    monitor.start_monitoring()

    current["sent"] += 5000
    clock["time"] += 1

    stats = monitor.get_network_stats()

    assert len(stats["alerts"]) == 1
    assert (
        stats["alerts"][0]["event_type"]
        == "UPLOAD_THRESHOLD_EXCEEDED"
    )


def test_no_alert_below_threshold(monkeypatch):
    current, clock = setup_monitor(monkeypatch)

    monitor = NetworkMonitor(
        download_threshold=10000,
        upload_threshold=10000
    )
    monitor.start_monitoring()

    current["sent"] += 100
    current["received"] += 100
    clock["time"] += 1

    stats = monitor.get_network_stats()

    assert stats["alerts"] == []


def test_repeated_alert_is_suppressed(monkeypatch):
    current, clock = setup_monitor(monkeypatch)

    monitor = NetworkMonitor(
        download_threshold=100,
        alert_cooldown=30
    )
    monitor.start_monitoring()

    current["received"] += 1000
    clock["time"] += 1

    first = monitor.get_network_stats()
    assert len(first["alerts"]) == 1

    current["received"] += 1000
    clock["time"] += 1

    second = monitor.get_network_stats()
    assert len(second["alerts"]) == 0


def test_alert_can_reoccur_after_usage_returns_below_threshold(
    monkeypatch
):
    current, clock = setup_monitor(monkeypatch)

    monitor = NetworkMonitor(
        download_threshold=100,
        alert_cooldown=30
    )
    monitor.start_monitoring()

    current["received"] += 1000
    clock["time"] += 1

    first = monitor.get_network_stats()
    assert len(first["alerts"]) == 1

    # Return below threshold.
    clock["time"] += 1
    monitor.get_network_stats()

    # Exceed threshold again.
    current["received"] += 1000
    clock["time"] += 1

    third = monitor.get_network_stats()
    assert len(third["alerts"]) == 1


def test_stop_monitoring(monkeypatch):
    current, clock = setup_monitor(monkeypatch)

    monitor = NetworkMonitor()
    monitor.start_monitoring()

    current["sent"] += 1000
    current["received"] += 2000
    clock["time"] += 2

    result = monitor.stop_monitoring()

    assert result["status"] == "stopped"
    assert monitor.is_monitoring is False
    assert result["session"]["end_time"] is not None


def test_cannot_collect_stats_before_start():
    monitor = NetworkMonitor()

    with pytest.raises(RuntimeError):
        monitor.get_network_stats()


def test_cannot_start_twice(monkeypatch):
    setup_monitor(monkeypatch)

    monitor = NetworkMonitor()
    monitor.start_monitoring()

    with pytest.raises(RuntimeError):
        monitor.start_monitoring()


def test_cannot_stop_when_not_monitoring():
    monitor = NetworkMonitor()

    with pytest.raises(RuntimeError):
        monitor.stop_monitoring()


@pytest.mark.parametrize(
    "value",
    [-1, True, "100", float("nan"), float("inf")]
)
def test_invalid_download_threshold(value):
    with pytest.raises(ValueError):
        NetworkMonitor(download_threshold=value)


def test_negative_upload_threshold():
    with pytest.raises(ValueError):
        NetworkMonitor(upload_threshold=-1)


def test_invalid_alert_cooldown():
    with pytest.raises(ValueError):
        NetworkMonitor(alert_cooldown=-1)


def test_network_counter_reset_does_not_create_negative_usage(
    monkeypatch
):
    current, clock = setup_monitor(monkeypatch)

    monitor = NetworkMonitor()
    monitor.start_monitoring()

    # Simulate interface counter reset.
    current["sent"] = 100
    current["received"] = 100
    clock["time"] += 1

    stats = monitor.get_network_stats()

    assert stats["upload_speed_bytes_per_second"] == 0
    assert stats["download_speed_bytes_per_second"] == 0
    assert stats["total_uploaded_bytes"] == 0
    assert stats["total_downloaded_bytes"] == 0
