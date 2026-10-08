import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from detection.detector import detect_throttling


def test_sustained_high_usage():
    cpu_history = [93, 95, 94, 96, 92]
    memory_history = [82, 84, 83, 85, 81]

    result = detect_throttling(cpu_history, memory_history)

    assert result is True


def test_normal_usage():
    cpu_history = [45, 50, 48, 52, 47]
    memory_history = [55, 58, 56, 54, 57]

    result = detect_throttling(cpu_history, memory_history)

    assert result is False


def test_single_cpu_spike():
    cpu_history = [45, 48, 97, 47, 50]
    memory_history = [55, 57, 85, 56, 54]

    result = detect_throttling(cpu_history, memory_history)

    assert result is False


def test_empty_cpu_history():
    cpu_history = []
    memory_history = [55, 58, 56]

    result = detect_throttling(cpu_history, memory_history)

    assert result is False


def test_empty_memory_history():
    cpu_history = [90, 92, 91]
    memory_history = []

    result = detect_throttling(cpu_history, memory_history)

    assert result is False
