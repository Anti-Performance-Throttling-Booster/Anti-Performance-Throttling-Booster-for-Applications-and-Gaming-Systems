
import math
import time
from datetime import datetime, timezone

import psutil


class NetworkMonitor:
    """
    Monitors total system network usage.

    Tracks download/upload speeds, transferred data, monitoring
    duration, and configurable usage-threshold alerts.

    This monitors aggregate network traffic. It does not inspect
    private application content or identify individual app traffic.
    """

    def __init__(
        self,
        download_threshold=None,
        upload_threshold=None,
        alert_cooldown=30
    ):
        self._validate_threshold(download_threshold, "Download threshold")
        self._validate_threshold(upload_threshold, "Upload threshold")
        self._validate_threshold(alert_cooldown, "Alert cooldown")

        self.download_threshold = download_threshold
        self.upload_threshold = upload_threshold
        self.alert_cooldown = float(alert_cooldown)

        self.is_monitoring = False
        self.start_time = None
        self.end_time = None

        self._start_monotonic = None
        self._last_monotonic = None
        self._last_counters = None

        self._total_uploaded = 0
        self._total_downloaded = 0

        self._alerts = []
        self._active_alerts = set()
        self._last_alert_time = {}

    @staticmethod
    def _validate_threshold(value, field_name):
        """Validate a threshold or cooldown value."""
        if value is None:
            return

        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            raise ValueError(
                f"{field_name} must be a finite non-negative number or None."
            )

    @staticmethod
    def _get_counters():
        """Get aggregate network byte counters from the operating system."""
        counters = psutil.net_io_counters(pernic=False)

        if counters is None:
            raise RuntimeError("Unable to retrieve network counters.")

        return {
            "bytes_sent": counters.bytes_sent,
            "bytes_recv": counters.bytes_recv
        }

    @staticmethod
    def _safe_delta(current, previous):
        """Calculate a non-negative counter difference."""
        difference = current - previous
        return max(0, difference)

    @staticmethod
    def _utc_now():
        """Return the current UTC timestamp."""
        return datetime.now(timezone.utc)

    def start_monitoring(self):
        """Start a new network monitoring session."""
        if self.is_monitoring:
            raise RuntimeError("Monitoring is already running.")

        counters = self._get_counters()
        current_time = time.monotonic()

        self.start_time = self._utc_now()
        self.end_time = None

        self._start_monotonic = current_time
        self._last_monotonic = current_time
        self._last_counters = counters

        self._total_uploaded = 0
        self._total_downloaded = 0

        self._alerts = []
        self._active_alerts = set()
        self._last_alert_time = {}

        self.is_monitoring = True

        return {
            "status": "started",
            "start_time": self.start_time.isoformat()
        }

    def _create_alert(self, event_type, current_value, threshold):
        """Create a timestamped threshold alert."""
        return {
            "event_type": event_type,
            "timestamp": self._utc_now().isoformat(),
            "current_value_bytes_per_second": current_value,
            "threshold_bytes_per_second": threshold,
            "message": (
                f"{event_type}: network usage exceeded "
                f"the configured threshold."
            )
        }

    def _check_one_threshold(
        self,
        event_type,
        current_value,
        threshold
    ):
        """Check one threshold and apply alert cooldown."""
        if threshold is None:
            self._active_alerts.discard(event_type)
            return None

        if current_value <= threshold:
            self._active_alerts.discard(event_type)
            return None

        now = time.monotonic()

        if event_type in self._active_alerts:
            last_alert = self._last_alert_time.get(event_type, now)

            if now - last_alert < self.alert_cooldown:
                return None

        alert = self._create_alert(
            event_type,
            current_value,
            threshold
        )

        self._active_alerts.add(event_type)
        self._last_alert_time[event_type] = now
        self._alerts.append(alert)

        return alert

    def check_thresholds(self, download_speed, upload_speed):
        """Check download and upload speeds against configured limits."""
        new_alerts = []

        download_alert = self._check_one_threshold(
            "DOWNLOAD_THRESHOLD_EXCEEDED",
            download_speed,
            self.download_threshold
        )

        upload_alert = self._check_one_threshold(
            "UPLOAD_THRESHOLD_EXCEEDED",
            upload_speed,
            self.upload_threshold
        )

        if download_alert is not None:
            new_alerts.append(download_alert)

        if upload_alert is not None:
            new_alerts.append(upload_alert)

        return new_alerts

    def get_network_stats(self):
        """Collect current network usage statistics."""
        if not self.is_monitoring:
            raise RuntimeError(
                "Start monitoring before collecting network statistics."
            )

        current_counters = self._get_counters()
        current_time = time.monotonic()

        elapsed = current_time - self._last_monotonic

        if elapsed <= 0:
            elapsed = 0.000001

        uploaded_delta = self._safe_delta(
            current_counters["bytes_sent"],
            self._last_counters["bytes_sent"]
        )

        downloaded_delta = self._safe_delta(
            current_counters["bytes_recv"],
            self._last_counters["bytes_recv"]
        )

        upload_speed = uploaded_delta / elapsed
        download_speed = downloaded_delta / elapsed

        self._total_uploaded += uploaded_delta
        self._total_downloaded += downloaded_delta

        new_alerts = self.check_thresholds(
            download_speed,
            upload_speed
        )

        self._last_counters = current_counters
        self._last_monotonic = current_time

        duration = current_time - self._start_monotonic

        return {
            "timestamp": self._utc_now().isoformat(),
            "monitoring_period_start": self.start_time.isoformat(),
            "duration_seconds": duration,

            "upload_speed_bytes_per_second": upload_speed,
            "download_speed_bytes_per_second": download_speed,

            "upload_speed_mb_per_second": (
                upload_speed / (1024 * 1024)
            ),
            "download_speed_mb_per_second": (
                download_speed / (1024 * 1024)
            ),

            "total_uploaded_bytes": self._total_uploaded,
            "total_downloaded_bytes": self._total_downloaded,

            "total_uploaded_mb": (
                self._total_uploaded / (1024 * 1024)
            ),
            "total_downloaded_mb": (
                self._total_downloaded / (1024 * 1024)
            ),

            "alerts": new_alerts
        }

    def get_session_stats(self):
        """Return statistics for the current or completed session."""
        if self.start_time is None:
            raise RuntimeError("Monitoring has not been started.")

        if self.is_monitoring:
            duration = time.monotonic() - self._start_monotonic
            end_time = None
        else:
            duration = (
                self.end_time - self.start_time
            ).total_seconds()
            end_time = self.end_time.isoformat()

        return {
            "start_time": self.start_time.isoformat(),
            "end_time": end_time,
            "duration_seconds": max(0, duration),
            "total_uploaded_bytes": self._total_uploaded,
            "total_downloaded_bytes": self._total_downloaded,
            "is_monitoring": self.is_monitoring
        }

    def get_recent_alerts(self, limit=10):
        """Return the most recent threshold alerts."""
        if (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or limit < 1
        ):
            raise ValueError("Limit must be a positive integer.")

        return self._alerts[-limit:]

    def stop_monitoring(self):
        """Stop monitoring and return the final session statistics."""
        if not self.is_monitoring:
            raise RuntimeError("Monitoring is not currently running.")

        # Take one final sample before stopping.
        self.get_network_stats()

        self.end_time = self._utc_now()
        self.is_monitoring = False

        return {
            "status": "stopped",
            "session": self.get_session_stats()
        }
