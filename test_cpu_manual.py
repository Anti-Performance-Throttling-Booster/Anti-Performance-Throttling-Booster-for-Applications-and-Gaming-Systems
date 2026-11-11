# test_cpu_manual.py

from monitoring.cpu_monitor import CPUMonitor


cpu = CPUMonitor()

print("Logical CPU cores:", cpu.get_core_count())

print("Overall CPU usage:", cpu.get_usage(), "%")

print("Per-core CPU usage:", cpu.get_per_core_usage())
