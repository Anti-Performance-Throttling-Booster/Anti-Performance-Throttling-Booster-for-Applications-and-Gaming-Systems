# Member 3 - Test Plan

Module owner: Harshitha Vangaveti  
Functional requirements: REQ-09 to REQ-12 and REQ-16 to REQ-19  
Test types: Unit (UT), Integration (IT), System (ST)

> Fill **Actual Result** and **Test Result** only after executing each test on the project build. The expected results below are the pass criteria; do not pre-mark manual tests as passed.

## A. Background Process Optimization - REQ-09 to REQ-12

| Test ID | Type | Preconditions | Steps | Test data | Expected result | Actual result | Test result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M3-OPT-01 | UT | ProcessAnalyzer available; Gaming profile active | 1. Pass a valid process list to the analyzer. 2. Inspect returned rows. | PID 202, Browser.exe, CPU 25%, memory 700 MB | Process name, PID, CPU and memory values are returned correctly and rows are sorted by resource usage. | To be filled | To be filled |
| M3-OPT-02 | UT | Gaming profile active; target PID selected | 1. Analyze a process whose CPU usage exceeds the profile threshold. 2. Inspect eligibility. | Target PID 101; Browser PID 202; CPU 25% | Non-protected high-CPU process is marked as a potential candidate and eligible for a confirmed priority change. | To be filled | To be filled |
| M3-OPT-03 | UT | Gaming profile active; target PID selected | 1. Analyze a memory-heavy but low-CPU process. 2. Attempt to optimize it. | CPU 1%; memory 4096 MB; profile memory threshold 1024 MB | Process is marked memory-heavy for review but is not automatically optimized, because lowering CPU priority does not free RAM. | To be filled | To be filled |
| M3-OPT-04 | UT | Process protection rules loaded | 1. Pass a critical process in the process list. 2. Attempt optimization. | `svchost.exe`, CPU 40% | Process is marked protected; no priority setter is called. | To be filled | To be filled |
| M3-OPT-05 | UT | User-selected target PID is known | 1. Pass the target process to the analyzer. 2. Attempt optimization on that PID. | Target `Game.exe`, PID 101 | Target game is protected and cannot be selected for optimization. | To be filled | To be filled |
| M3-OPT-06 | UT | Eligible candidate exists; fake adapter used | 1. Call optimization with `confirmed=False`. 2. Inspect result and adapter calls. | PID 202; confirmed False | Status is `cancelled`; no process priority change is attempted. | To be filled | To be filled |
| M3-OPT-07 | UT | Eligible candidate exists; fake adapter used | 1. Call optimization with `confirmed=True`. 2. Inspect adapter call and result. | PID 202; target PID 101 | Adapter is asked to set below-normal priority; result reports success, process, profile, timestamp and message. | To be filled | To be filled |
| M3-OPT-08 | UT | Fake adapter configured to raise PermissionError | 1. Confirm optimization of an eligible process. 2. Simulate OS permission denial. | PID 202; `PermissionError` | Result reports failure clearly; application does not crash or claim success. | To be filled | To be filled |
| M3-OPT-09 | IT | Member 1 monitoring code is available on the integrated branch | 1. Start MonitoringEngine. 2. Wait for first collection. 3. Read `get_metrics()`. 4. Pass `metrics["processes"]` to OptimizationEngine. | Process snapshot from MonitoringEngine | Member 3 analyzer consumes Member 1's process-list schema without changing Member 1's module; `None` before first sample is handled by the caller. | To be filled | To be filled |
| M3-OPT-10 | ST | Integrated dashboard, monitoring and Member 3 module available | 1. Start monitoring. 2. Select target game. 3. Select an eligible candidate. 4. Cancel confirmation, then repeat and accept. 5. Inspect displayed action result. | Selected game PID plus one safe test process | Cancel causes no action; accepting causes one permitted priority change; success/failure is visible to the user and supplied to Member 4's logger. | To be filled | To be filled |

## B. User-Controlled Performance Profiles - REQ-16 to REQ-19

| Test ID | Type | Preconditions | Steps | Test data | Expected result | Actual result | Test result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M3-PRO-01 | UT | ProfileManager initialized with a temporary settings file | 1. List available profiles. 2. Inspect names and settings. | Default configuration | Gaming, Balanced and Conservative profiles are available with valid thresholds and action limits. | To be filled | To be filled |
| M3-PRO-02 | UT | No saved profile state exists | 1. Create ProfileManager. 2. Read active profile. | Empty settings path | Balanced is selected by default. | To be filled | To be filled |
| M3-PRO-03 | UT | ProfileManager initialized | 1. Select Gaming. 2. Read active profile. | Profile name `Gaming` | Gaming becomes the active profile and its settings are returned. | To be filled | To be filled |
| M3-PRO-04 | UT | ProfileManager initialized | 1. Select a non-existent profile. 2. Inspect error. | `Ultra Turbo` | A clear KeyError is raised; active profile remains unchanged. | To be filled | To be filled |
| M3-PRO-05 | UT | Gaming profile exists | 1. Update CPU threshold and max actions. 2. Read profile. | CPU threshold 7.5%; max actions 2 | Supported settings are updated and returned accurately. | To be filled | To be filled |
| M3-PRO-06 | UT | ProfileManager initialized | 1. Try an invalid CPU threshold. 2. Try max actions outside the allowed range. | CPU 101%; max actions 0 | Invalid settings are rejected with a validation error; previous valid values remain. | To be filled | To be filled |
| M3-PRO-07 | UT | Writable temporary settings file | 1. Select Gaming and modify a setting. 2. Construct a new ProfileManager using the same file. | Gaming; CPU threshold 7.5% | Active profile and customized settings persist after reload. | To be filled | To be filled |
| M3-PRO-08 | UT | ProfileManager initialized | 1. Create a custom profile. 2. Retrieve it by name. | My Profile; CPU 12%; memory 1800 MB; max actions 2 | Custom profile is created and appears in the profile list. Duplicate or invalid names are rejected. | To be filled | To be filled |
| M3-PRO-09 | IT | ProcessAnalyzer and ProfileManager connected | 1. Analyze the same process snapshot using Gaming. 2. Select Conservative. 3. Analyze again. | Same process CPU 8%; Gaming threshold 5%; Conservative threshold 15% | Candidate eligibility changes according to the active profile; the engine does not use hard-coded thresholds from another profile. | To be filled | To be filled |
| M3-PRO-10 | ST | Profile controls integrated in dashboard | 1. Open profile controls. 2. Select a profile. 3. Modify supported settings. 4. Refresh process recommendations. 5. Restart app and inspect saved settings. | Gaming then modified threshold | Dashboard shows selected profile; modified settings affect optimization decisions and persist after restart. | To be filled | To be filled |

## Execution notes

- Unit tests in `tests/test_profiles.py` and `tests/test_optimization.py` use a fake priority adapter. They do not change real process priorities.
- For integration and system tests, use the integrated monitoring/dashboard branch and a harmless test process. Never test by targeting Windows critical processes or the application/game being protected.
- Record screenshots or terminal output for evidence, and record the actual result before marking Pass/Fail.
