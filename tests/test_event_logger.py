
import json
from datetime import datetime

import pytest

from logging_module.event_logger import EventLogger


def test_logger_creates_log_directory(tmp_path):
    log_dir = tmp_path / "logs"

    logger = EventLogger(log_dir=str(log_dir))

    assert log_dir.exists()
    assert logger.log_file.exists() is False


def test_log_throttling_event(tmp_path):
    logger = EventLogger(log_dir=str(tmp_path))

    event = logger.log_throttling_event(
        "High network usage detected",
        source="mock_detector",
        details={"download_speed_mbps": 15.5}
    )

    assert event["event_type"] == "THROTTLING_DETECTED"
    assert event["source"] == "mock_detector"
    assert event["message"] == "High network usage detected"
    assert event["details"]["download_speed_mbps"] == 15.5


def test_log_optimization_action(tmp_path):
    logger = EventLogger(log_dir=str(tmp_path))

    event = logger.log_optimization_action(
        "Background process optimized",
        source="mock_optimizer",
        details={"action": "reduce_background_usage"}
    )

    assert event["event_type"] == "OPTIMIZATION_ACTION"
    assert event["source"] == "mock_optimizer"
    assert event["details"]["action"] == "reduce_background_usage"


def test_event_contains_valid_utc_timestamp(tmp_path):
    logger = EventLogger(log_dir=str(tmp_path))

    event = logger.log_event(
        "TEST_EVENT",
        "Testing timestamp"
    )

    timestamp = datetime.fromisoformat(event["timestamp"])

    assert timestamp.tzinfo is not None
    assert timestamp.utcoffset().total_seconds() == 0


def test_event_is_saved_as_json_line(tmp_path):
    logger = EventLogger(log_dir=str(tmp_path))

    logger.log_event(
        "TEST_EVENT",
        "Testing JSON storage"
    )

    with logger.log_file.open("r", encoding="utf-8") as file:
        saved_event = json.loads(file.readline())

    assert saved_event["event_type"] == "TEST_EVENT"
    assert saved_event["message"] == "Testing JSON storage"


def test_get_recent_logs_returns_events(tmp_path):
    logger = EventLogger(log_dir=str(tmp_path))

    logger.log_throttling_event("Throttling detected")
    logger.log_optimization_action("Optimization completed")

    logs = logger.get_recent_logs()

    assert len(logs) == 2
    assert logs[0]["event_type"] == "THROTTLING_DETECTED"
    assert logs[1]["event_type"] == "OPTIMIZATION_ACTION"


def test_get_recent_logs_respects_limit(tmp_path):
    logger = EventLogger(log_dir=str(tmp_path))

    for number in range(5):
        logger.log_event(
            "TEST_EVENT",
            f"Event {number}"
        )

    logs = logger.get_recent_logs(limit=2)

    assert len(logs) == 2
    assert logs[0]["message"] == "Event 3"
    assert logs[1]["message"] == "Event 4"


def test_get_recent_logs_returns_empty_list_when_no_file_exists(tmp_path):
    logger = EventLogger(log_dir=str(tmp_path))

    assert logger.get_recent_logs() == []


def test_log_file_path_returns_path(tmp_path):
    logger = EventLogger(log_dir=str(tmp_path))

    assert logger.get_log_file_path().endswith("events.jsonl")


def test_empty_event_type_is_rejected(tmp_path):
    logger = EventLogger(log_dir=str(tmp_path))

    with pytest.raises(ValueError):
        logger.log_event("", "Test message")


def test_empty_message_is_rejected(tmp_path):
    logger = EventLogger(log_dir=str(tmp_path))

    with pytest.raises(ValueError):
        logger.log_event("TEST_EVENT", "  ")


def test_empty_source_is_rejected(tmp_path):
    logger = EventLogger(log_dir=str(tmp_path))

    with pytest.raises(ValueError):
        logger.log_event(
            "TEST_EVENT",
            "Test message",
            source=""
        )


def test_details_must_be_dictionary(tmp_path):
    logger = EventLogger(log_dir=str(tmp_path))

    with pytest.raises(ValueError):
        logger.log_event(
            "TEST_EVENT",
            "Test message",
            details="invalid details"
        )


def test_non_json_details_are_rejected(tmp_path):
    logger = EventLogger(log_dir=str(tmp_path))

    with pytest.raises(ValueError):
        logger.log_event(
            "TEST_EVENT",
            "Test message",
            details={"invalid": object()}
        )


def test_nan_details_are_rejected(tmp_path):
    logger = EventLogger(log_dir=str(tmp_path))

    with pytest.raises(ValueError):
        logger.log_event(
            "TEST_EVENT",
            "Test message",
            details={"value": float("nan")}
        )


def test_invalid_log_limit_is_rejected(tmp_path):
    logger = EventLogger(log_dir=str(tmp_path))

    with pytest.raises(ValueError):
        logger.get_recent_logs(limit=0)

    with pytest.raises(ValueError):
        logger.get_recent_logs(limit=-1)

    with pytest.raises(ValueError):
        logger.get_recent_logs(limit=True)


def test_invalid_filename_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        EventLogger(
            log_dir=str(tmp_path),
            filename="events.txt"
        )


def test_filename_with_directory_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        EventLogger(
            log_dir=str(tmp_path),
            filename="folder/events.jsonl"
        )


def test_malformed_json_lines_are_skipped(tmp_path):
    logger = EventLogger(log_dir=str(tmp_path))

    logger.log_event("TEST_EVENT", "Valid event")

    with logger.log_file.open("a", encoding="utf-8") as file:
        file.write("This is not valid JSON\n")

    logger.log_event("TEST_EVENT", "Another valid event")

    logs = logger.get_recent_logs()

    assert len(logs) == 2
    assert logs[0]["message"] == "Valid event"
    assert logs[1]["message"] == "Another valid event"


def test_multiple_events_are_appended(tmp_path):
    logger = EventLogger(log_dir=str(tmp_path))

    logger.log_event("EVENT_ONE", "First event")
    logger.log_event("EVENT_TWO", "Second event")
    logger.log_event("EVENT_THREE", "Third event")

    logs = logger.get_recent_logs()

    assert len(logs) == 3
    assert logs[0]["event_type"] == "EVENT_ONE"
    assert logs[1]["event_type"] == "EVENT_TWO"
    assert logs[2]["event_type"] == "EVENT_THREE"
