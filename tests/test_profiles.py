import pytest

from optimization.profiles import ProfileManager


def test_predefined_profiles_are_available(tmp_path):
    manager = ProfileManager(tmp_path / "profiles.json")
    assert {p.name for p in manager.list_profiles()} >= {"Gaming", "Balanced", "Conservative"}
    assert manager.active_profile.name == "Balanced"


def test_select_profile_is_persisted(tmp_path):
    file_path = tmp_path / "profiles.json"
    manager = ProfileManager(file_path)
    manager.select_profile("Gaming")

    reloaded = ProfileManager(file_path)
    assert reloaded.active_profile.name == "Gaming"


def test_update_profile_changes_settings_and_persists(tmp_path):
    file_path = tmp_path / "profiles.json"
    manager = ProfileManager(file_path)
    manager.update_profile("Gaming", cpu_threshold_percent=7.5, max_actions=2)

    reloaded = ProfileManager(file_path)
    assert reloaded.get_profile("Gaming").cpu_threshold_percent == 7.5
    assert reloaded.get_profile("Gaming").max_actions == 2


def test_create_custom_profile(tmp_path):
    manager = ProfileManager(tmp_path / "profiles.json")
    created = manager.create_profile("My Profile", 12, 1800, 2)
    assert created.name == "My Profile"
    assert manager.get_profile("My Profile").memory_threshold_mb == 1800


def test_reject_invalid_cpu_threshold(tmp_path):
    manager = ProfileManager(tmp_path / "profiles.json")
    with pytest.raises(ValueError):
        manager.update_profile("Gaming", cpu_threshold_percent=101)


def test_reject_invalid_max_actions(tmp_path):
    manager = ProfileManager(tmp_path / "profiles.json")
    with pytest.raises(ValueError):
        manager.update_profile("Gaming", max_actions=0)
