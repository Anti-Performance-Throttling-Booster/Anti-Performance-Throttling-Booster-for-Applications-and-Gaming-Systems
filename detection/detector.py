
from datetime import datetime


def detect_throttling(cpu_history, memory_history):
    """Detect sustained high CPU and memory usage."""
    if not cpu_history or not memory_history:
        return False

    if len(cpu_history) != len(memory_history):
        return False

    cpu_high = all(cpu >= 90 for cpu in cpu_history)
    memory_high = all(memory >= 80 for memory in memory_history)

    return cpu_high and memory_high


def record_event(
    cpu_history,
    memory_history,
    process_name,
    process_cpu_usage,
    process_memory_usage
):
    """Record details of a suspected throttling event."""
    if not cpu_history or not memory_history:
        raise ValueError("CPU and memory histories must not be empty.")

    event = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cpu_usage": cpu_history[-1],
        "memory_usage": memory_history[-1],
        "process_name": process_name,
        "process_cpu_usage": process_cpu_usage,
        "process_memory_usage": process_memory_usage,
        "event_type": "Suspected performance throttling"
    }

    return event


def display_alert(event):
    """Display an alert for a suspected throttling event."""
    print()
    print("========================================")
    print("WARNING: Suspected performance throttling detected!")
    print("========================================")
    print("Time:", event["timestamp"])
    print("Process:", event["process_name"])
    print("CPU Usage:", event["cpu_usage"], "%")
    print("Memory Usage:", event["memory_usage"], "%")
    print("Process CPU Usage:", event["process_cpu_usage"], "%")
    print("Process Memory Usage:", event["process_memory_usage"], "%")
    print("========================================")


def generate_recommendation(cpu_usage, memory_usage):
    """Generate a basic recommendation from the supplied metrics."""
    if cpu_usage >= 90 and memory_usage >= 80:
        return (
            "High CPU and memory usage detected. "
            "Consider closing unnecessary background applications."
        )

    if cpu_usage >= 90:
        return (
            "High CPU usage detected. "
            "Consider closing unnecessary background applications."
        )

    if memory_usage >= 80:
        return (
            "High memory usage detected. "
            "Consider closing unnecessary background applications."
        )

    return "No optimization recommendation available."
