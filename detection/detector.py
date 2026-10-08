def detect_throttling(cpu_usage, memory_usage):
    if cpu_usage >= 90 and memory_usage >= 80:
        return True
    return False


cpu = 95
memory = 85

result = detect_throttling(cpu, memory)

if result:
    print("Suspected performance throttling")
else:
    print("No suspected throttling")