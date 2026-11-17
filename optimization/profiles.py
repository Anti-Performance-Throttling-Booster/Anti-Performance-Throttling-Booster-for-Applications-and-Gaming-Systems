"""Predefined and user-configurable performance profiles."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json
import math
from pathlib import Path
from typing import Any


DEFAULT_PROFILES: dict[str, dict[str, Any]] = {
    # Thresholds are initial project defaults. Tune them after observing test data.
    "Gaming": {
        "cpu_threshold_percent": 5.0,
        "memory_threshold_mb": 1024.0,
        "max_actions": 3,
    },
    "Balanced": {
        "cpu_threshold_percent": 10.0,
        "memory_threshold_mb": 2048.0,
        "max_actions": 2,
    },
    "Conservative": {
        "cpu_threshold_percent": 15.0,
        "memory_threshold_mb": 3072.0,
        "max_actions": 1,
    },
}


@dataclass(frozen=True)
class PerformanceProfile:
    """Settings that control which processes may be considered for optimization."""

    name: str
    cpu_threshold_percent: float
    memory_threshold_mb: float
    max_actions: int
    priority_target: str = "below_normal"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProfileManager:
    """Load, select, create, modify, and persist performance profiles."""

    def __init__(self, storage_path: str | Path | None = None) -> None:
        if storage_path is None:
            project_root = Path(__file__).resolve().parent.parent
            storage_path = project_root / "data" / "profiles.json"

        self.storage_path = Path(storage_path)
        self._profiles: dict[str, PerformanceProfile] = {}
        self._active_profile_name = "Balanced"
        self._load_defaults()
        self._load_from_disk()

    @property
    def active_profile(self) -> PerformanceProfile:
        return self.get_profile(self._active_profile_name)

    @property
    def active_profile_name(self) -> str:
        return self._active_profile_name

    def list_profiles(self) -> list[PerformanceProfile]:
        return list(self._profiles.values())

    def get_profile(self, name: str | None = None) -> PerformanceProfile:
        selected_name = name or self._active_profile_name
        key = self._find_profile_key(selected_name)
        if key is None:
            raise KeyError(f"Profile '{selected_name}' does not exist.")
        return self._profiles[key]

    def select_profile(self, name: str) -> PerformanceProfile:
        key = self._find_profile_key(name)
        if key is None:
            raise KeyError(f"Profile '{name}' does not exist.")
        self._active_profile_name = key
        self._save_to_disk()
        return self._profiles[key]

    def create_profile(
        self,
        name: str,
        cpu_threshold_percent: float,
        memory_threshold_mb: float,
        max_actions: int,
    ) -> PerformanceProfile:
        clean_name = self._validate_name(name)
        if self._find_profile_key(clean_name) is not None:
            raise ValueError(f"A profile named '{clean_name}' already exists.")

        profile = self._make_profile(
            clean_name,
            cpu_threshold_percent,
            memory_threshold_mb,
            max_actions,
        )
        self._profiles[clean_name] = profile
        self._save_to_disk()
        return profile

    def update_profile(
        self,
        name: str,
        *,
        cpu_threshold_percent: float | None = None,
        memory_threshold_mb: float | None = None,
        max_actions: int | None = None,
    ) -> PerformanceProfile:
        key = self._find_profile_key(name)
        if key is None:
            raise KeyError(f"Profile '{name}' does not exist.")

        current = self._profiles[key]
        updated = self._make_profile(
            key,
            current.cpu_threshold_percent if cpu_threshold_percent is None else cpu_threshold_percent,
            current.memory_threshold_mb if memory_threshold_mb is None else memory_threshold_mb,
            current.max_actions if max_actions is None else max_actions,
        )
        self._profiles[key] = updated
        self._save_to_disk()
        return updated

    def _load_defaults(self) -> None:
        self._profiles = {
            name: self._make_profile(
                name,
                settings["cpu_threshold_percent"],
                settings["memory_threshold_mb"],
                settings["max_actions"],
            )
            for name, settings in DEFAULT_PROFILES.items()
        }

    def _load_from_disk(self) -> None:
        if not self.storage_path.exists():
            return

        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
            stored_profiles = data.get("profiles", {})
            if not isinstance(stored_profiles, dict):
                return

            loaded: dict[str, PerformanceProfile] = {}
            for name, settings in stored_profiles.items():
                if not isinstance(settings, dict):
                    continue
                loaded[name] = self._make_profile(
                    name,
                    settings.get("cpu_threshold_percent"),
                    settings.get("memory_threshold_mb"),
                    settings.get("max_actions"),
                )

            # Keep defaults available even if a saved file contains only custom profiles.
            for name, profile in self._profiles.items():
                loaded.setdefault(name, profile)
            self._profiles = loaded

            requested_active = data.get("active_profile", "Balanced")
            active_key = self._find_profile_key(requested_active)
            self._active_profile_name = active_key or "Balanced"
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            # A damaged settings file must never stop the application from starting.
            self._load_defaults()
            self._active_profile_name = "Balanced"

    def _save_to_disk(self) -> None:
        payload = {
            "active_profile": self._active_profile_name,
            "profiles": {
                name: profile.to_dict()
                for name, profile in self._profiles.items()
            },
        }
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.storage_path.with_suffix(self.storage_path.suffix + ".tmp")
        temporary_path.write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
        temporary_path.replace(self.storage_path)

    def _find_profile_key(self, name: str) -> str | None:
        if not isinstance(name, str):
            return None
        normalized = name.strip().casefold()
        for existing_name in self._profiles:
            if existing_name.casefold() == normalized:
                return existing_name
        return None

    @staticmethod
    def _validate_name(name: str) -> str:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Profile name must be a non-empty string.")
        return name.strip()

    @classmethod
    def _make_profile(
        cls,
        name: str,
        cpu_threshold_percent: float,
        memory_threshold_mb: float,
        max_actions: int,
    ) -> PerformanceProfile:
        clean_name = cls._validate_name(name)
        cpu_threshold = cls._validate_number(
            cpu_threshold_percent,
            "CPU threshold",
            minimum=0.1,
            maximum=100.0,
        )
        memory_threshold = cls._validate_number(
            memory_threshold_mb,
            "Memory threshold",
            minimum=1.0,
            maximum=1_000_000.0,
        )
        if isinstance(max_actions, bool) or not isinstance(max_actions, int):
            raise ValueError("Maximum actions must be a whole number from 1 to 10.")
        if not 1 <= max_actions <= 10:
            raise ValueError("Maximum actions must be between 1 and 10.")

        return PerformanceProfile(
            name=clean_name,
            cpu_threshold_percent=cpu_threshold,
            memory_threshold_mb=memory_threshold,
            max_actions=max_actions,
            priority_target="below_normal",
        )

    @staticmethod
    def _validate_number(
        value: float,
        label: str,
        *,
        minimum: float,
        maximum: float,
    ) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{label} must be numeric.")
        if not math.isfinite(float(value)) or not minimum <= float(value) <= maximum:
            raise ValueError(f"{label} must be between {minimum:g} and {maximum:g}.")
        return float(value)
