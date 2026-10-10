# test_process_manual.py

from monitoring.process_monitor import ProcessMonitor

monitor = ProcessMonitor()

processes = monitor.get_all_processes()

print("Total accessible processes:", len(processes))

print("\nTop CPU processes:")
for process in monitor.get_top_cpu_processes(5):
    print(
        f"PID: {process['pid']:<7} "
        f"Name: {process['name']:<25} "
        f"CPU: {process['cpu_percent']:.1f}% "
        f"Memory: {process['memory_mb']:.1f} MB"
    )

print("\nTop memory processes:")
for process in monitor.get_top_memory_processes(5):
    print(
        f"PID: {process['pid']:<7} "
        f"Name: {process['name']:<25} "
        f"Memory: {process['memory_mb']:.1f} MB"
    )
