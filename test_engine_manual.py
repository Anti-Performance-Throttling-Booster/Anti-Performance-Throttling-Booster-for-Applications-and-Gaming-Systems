# test_engine_manual.py

import time

from monitoring.engine import MonitoringEngine


engine = MonitoringEngine(refresh_interval=1.0)

print("Initial state:", engine.is_running)

print("\nStarting monitoring...")
engine.start()

print("Running state:", engine.is_running)

# Allow time for the first collection cycle.
time.sleep(3)

metrics = engine.get_metrics()

if metrics is not None:
    print("\nTimestamp:", metrics["timestamp"])

    print(
        "CPU usage:",
        metrics["cpu"]["usage_percent"],
        "%"
    )

    print(
        "Memory usage:",
        metrics["memory"]["usage_percent"],
        "%"
    )

    print(
        "Accessible processes:",
        len(metrics["processes"])
    )
else:
    print("No metrics collected yet.")

print("\nStopping monitoring...")
engine.stop()

print("Running state:", engine.is_running)
print("Monitoring stopped.")
