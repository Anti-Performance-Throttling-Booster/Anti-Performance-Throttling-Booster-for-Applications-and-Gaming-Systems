
import json
import threading
from collections import deque
from datetime import datetime, timezone
from pathlib import Path


class EventLogger:
    """
    Stores application monitoring events in a JSON Lines file.

    Supports:
    - Throttling event logging.
    - Optimization action logging.
    - Timestamped event records.
    - Retrieving recent logs.
    - Independent operation using mock events.

    The logger stores event metadata and supplied details only.
    It does not capture private application content.
    """

    def __init__(self, log_dir="logs", filename="events.jsonl"):
        self.log_dir = Path(log_dir)
        self.filename = filename

        if not isinstance(filename, str) or not filename.strip():
            raise ValueError("Log filename must be a non-empty string.")

        if Path(filename).name != filename:
            raise ValueError("Filename must not contain a directory path.")

        if not filename.endswith(".jsonl"):
            raise ValueError("Log filename must end with .jsonl.")

        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / filename

        self._lock = threading.Lock()

    @staticmethod
    def _validate_text(value, field_name):
        """Validate required text fields."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string.")

        return value.strip()

    @staticmethod
    def _validate_details(details):
        """Ensure event details can safely be serialized as JSON."""
        if details is None:
            return {}

        if not isinstance(details, dict):
            raise ValueError("Event details must be a dictionary.")

        try:
            # Reject non-JSON values and NaN/infinity.
            json.dumps(details, allow_nan=False)
        except (TypeError, ValueError) as error:
            raise ValueError(
                "Event details must contain valid JSON-compatible values."
            ) from error

        return details

    @staticmethod
    def _current_timestamp():
        """Generate a timezone-aware UTC timestamp."""
        return datetime.now(timezone.utc).isoformat()

    def log_event(
        self,
        event_type,
        message,
        source="system",
        details=None
    ):
        """
        Store a general event.

        Returns the event dictionary after successfully writing it.
        """
        event_type = self._validate_text(event_type, "Event type")
        message = self._validate_text(message, "Message")
        source = self._validate_text(source, "Source")
        details = self._validate_details(details)

        event = {
            "timestamp": self._current_timestamp(),
            "event_type": event_type,
            "source": source,
            "message": message,
            "details": details
        }

        serialized_event = json.dumps(
            event,
            ensure_ascii=False,
            allow_nan=False
        )

        # Lock prevents simultaneous writes from interleaving.
        with self._lock:
            with self.log_file.open(
                "a",
                encoding="utf-8"
            ) as file:
                file.write(serialized_event + "\n")

        return event

    def log_throttling_event(
        self,
        message,
        source="system",
        details=None
    ):
        """Record a detected throttling event."""
        return self.log_event(
            event_type="THROTTLING_DETECTED",
            message=message,
            source=source,
            details=details
        )

    def log_optimization_action(
        self,
        message,
        source="system",
        details=None
    ):
        """Record an optimization action."""
        return self.log_event(
            event_type="OPTIMIZATION_ACTION",
            message=message,
            source=source,
            details=details
        )

    def get_recent_logs(self, limit=20):
        """
        Retrieve the most recent log records.

        Returns records in chronological order (oldest first).
        Malformed JSON lines are skipped.
        """
        if (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or limit < 1
        ):
            raise ValueError("Limit must be a positive integer.")

        if not self.log_file.exists():
            return []

        recent_events = deque(maxlen=limit)

        with self._lock:
            with self.log_file.open(
                "r",
                encoding="utf-8"
            ) as file:
                for line in file:
                    line = line.strip()

                    if not line:
                        continue

                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if isinstance(event, dict):
                        recent_events.append(event)

        return list(recent_events)

    def get_log_file_path(self):
        """Return the location of the log file."""
        return str(self.log_file.resolve())
