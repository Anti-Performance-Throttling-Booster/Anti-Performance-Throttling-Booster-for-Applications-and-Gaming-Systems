
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from detection.detector import (
    detect_throttling,
    record_event,
    generate_recommendation,
    display_alert,
)


def test_sustained_high_usage():
    assert detect_throttling(
        [93, 95, 94, 96, 92],
        [82, 84, 83, 85, 81]
    ) is True


def test_normal_usage():
    assert detect_throttling(
        [45, 50, 48, 52, 47],
        [55, 58, 56, 54, 57]
    ) is False


def test_single_spike():
    assert detect_throttling(
        [45, 48, 97, 47, 50],
        [55, 57, 85, 56, 54]
    ) is False


def test_empty_cpu_history():
    assert detect_throttling([], [55, 58, 56]) is False


def test_empty_memory_history():
    assert detect_throttling([90, 92, 91], []) is False


def test_mismatched_history_lengths():
    assert detect_throttling([91, 92, 93], [81, 82]) is False


def test_record_event_contains_metrics():
    event = record_event(
        [93, 95, 94, 96, 92],
        [82, 84, 83, 85, 81],
        "ExampleGame.exe",
        72,
        65
    )

    assert event["cpu_usage"] == 92
    assert event["memory_usage"] == 81
    assert event["process_name"] == "ExampleGame.exe"
    assert event["process_cpu_usage"] == 72
    assert event["process_memory_usage"] == 65
    assert event["event_type"] == "Suspected performance throttling"


def test_record_event_has_timestamp():
    event = record_event([93], [82], "ExampleGame.exe", 72, 65)

    timestamp = datetime.strptime(
        event["timestamp"], "%Y-%m-%d %H:%M:%S"
    )

    assert isinstance(timestamp, datetime)


def test_record_event_rejects_empty_cpu_history():
    try:
        record_event([], [82], "ExampleGame.exe", 72, 65)
        assert False, "Expected ValueError for empty CPU history"
    except ValueError:
        pass


def test_record_event_rejects_empty_memory_history():
    try:
        record_event([93], [], "ExampleGame.exe", 72, 65)
        assert False, "Expected ValueError for empty memory history"
    except ValueError:
        pass


def test_high_cpu_and_memory_recommendation():
    recommendation = generate_recommendation(92, 81)
    assert "CPU and memory" in recommendation


def test_high_cpu_recommendation():
    recommendation = generate_recommendation(92, 60)
    assert "CPU usage" in recommendation


def test_high_memory_recommendation():
    recommendation = generate_recommendation(60, 81)
    assert "memory usage" in recommendation


def test_no_recommendation_for_normal_usage():
    recommendation = generate_recommendation(50, 60)
    assert recommendation == "No optimization recommendation available."


def test_alert_displays_warning(capsys):
    event = {
        "timestamp": "2026-10-09 18:00:00",
        "cpu_usage": 92,
        "memory_usage": 81,
        "process_name": "ExampleGame.exe",
        "process_cpu_usage": 72,
        "process_memory_usage": 65,
        "event_type": "Suspected performance throttling",
    }

    display_alert(event)
    output = capsys.readouterr().out

    assert "WARNING" in output
    assert "Suspected performance throttling detected" in output
    assert "ExampleGame.exe" in output
    assert "92" in output
    assert "81" in output


# Input validation tests

def test_rejects_negative_cpu_usage():
    try:
        detect_throttling([-10, 95], [82, 84])
        assert False, "Expected ValueError for negative CPU usage"
    except ValueError:
        pass


def test_rejects_cpu_usage_above_100():
    try:
        detect_throttling([95, 150], [82, 84])
        assert False, "Expected ValueError for CPU usage above 100"
    except ValueError:
        pass


def test_rejects_negative_memory_usage():
    try:
        detect_throttling([93, 95], [-5, 84])
        assert False, "Expected ValueError for negative memory usage"
    except ValueError:
        pass


def test_rejects_text_as_cpu_usage():
    try:
        generate_recommendation("high", 80)
        assert False, "Expected ValueError for text CPU usage"
    except ValueError:
        pass


def test_rejects_process_cpu_usage_above_100():
    try:
        record_event([93], [82], "ExampleGame.exe", 120, 65)
        assert False, "Expected ValueError for process CPU usage above 100"
    except ValueError:
        pass


def test_rejects_empty_process_name():
    try:
        record_event([93], [82], "   ", 72, 65)
        assert False, "Expected ValueError for an empty process name"
    except ValueError:
        pass
