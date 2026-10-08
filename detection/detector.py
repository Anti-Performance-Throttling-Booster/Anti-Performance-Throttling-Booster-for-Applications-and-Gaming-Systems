from datetime import datetime

def display_alert(event):
    print()
    print("========================================")
    print("WARNING: Suspected performance throttling detected!")
    print("========================================")
    print("Time:", event["timestamp"])
    print("CPU Usage:", event["cpu_usage"], "%")
    print("Memory Usage:", event["memory_usage"], "%")
    print("========================================")

def detect_throttling(cpu_history, memory_history):
    if len(cpu_history) == 0 or len(memory_history) == 0:
        return False

    cpu_high = all(cpu >= 90 for cpu in cpu_history)
    memory_high = all(memory >= 80 for memory in memory_history)

    if cpu_high and memory_high:
        return True

    return False


def record_event(cpu_history, memory_history):
    event = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cpu_usage": cpu_history[-1],
        "memory_usage": memory_history[-1],
        "event_type": "Suspected performance throttling"
    }

    return event


cpu_history = [93, 95, 94, 96, 92]
memory_history = [82, 84, 83, 85, 81]

result = detect_throttling(cpu_history, memory_history)

if result:
    event = record_event(cpu_history, memory_history)

    print("Suspected performance throttling")
    display_alert(event)
    print("Event Type:", event["event_type"])
else:
    print("No suspected throttling")