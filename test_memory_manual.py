# test_memory_manual.py

from monitoring.memory_monitor import MemoryMonitor


memory = MemoryMonitor()

print("Memory usage:", memory.get_memory_usage(), "%")

print(
    "Total memory:",
    round(memory.get_total_memory() / (1024 ** 3), 2),
    "GB"
)

print(
    "Used memory:",
    round(memory.get_used_memory() / (1024 ** 3), 2),
    "GB"
)

print(
    "Available memory:",
    round(memory.get_available_memory() / (1024 ** 3), 2),
    "GB"
)

print("Memory details:", memory.get_memory_details())
