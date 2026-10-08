def detect_throttling(cpu_history, memory_history):
    if len(cpu_history) == 0 or len(memory_history) == 0:
        return False

    cpu_high = all(cpu >= 90 for cpu in cpu_history)
    memory_high = all(memory >= 80 for memory in memory_history)

    if cpu_high and memory_high:
        return True

    return False


cpu_history = [45, 48, 97, 47, 50]
memory_history = [55, 57, 85, 56, 54]

result = detect_throttling(cpu_history, memory_history)

if result:
    print("Suspected performance throttling")
else:
    print("No suspected throttling")