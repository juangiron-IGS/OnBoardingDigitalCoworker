---
name: perf-timing
description: Measuring the Coworker's performance NFRs with scripts: package ready within 5 minutes (NFR-PERF-001), views within 2 seconds and chat receipt within 1 second (NFR-PERF-002), 10 simultaneous cases (NFR-PERF-003), model usage cap (NFR-PERF-004). Use when the PERF cases (QC-PERF-*) are run or their scripts written.
---

# Performance timing (scripted, localhost)

Plan: Test Plan §2.2 and §2.3 (QTOOL-003). The demo is single-user on localhost, so **no load-testing tool**; scripts are small and live in `code/tests/perf/` (create the folder; they are test code, not product code). Results go to `code/tests/evidence/perf-<date>.txt`.

- **NFR-PERF-001 (package Ready within 5 minutes of the last answer):** a Python script (or a pytest test marked `perf`) drives every seed scenario through the API or services, measuring with `time.perf_counter` and cross-checking the audit-log timestamps (last answer to the Ready transition). The limit applies to **every** case, not the average: report the maximum. With `MODEL_PROVIDER=rules` there is no model latency, so the result is a lower bound; say so, and run once more with `claude` if a key is available and the user agrees.
- **NFR-PERF-002 (views within 2 s, chat receipt within 1 s):** a Playwright script (Node or Python) opens each view on `http://127.0.0.1:3000` and reads the Navigation Timing API (`loadEventEnd - startTime`) plus the time from sending a chat message to the receipt indicator. Run each at least 5 times, report median and maximum. The 5-second threshold in the NFR needs its meaning confirmed (Test Cases QC-PERF-E-002): report against 2 s and flag the open point.
- **NFR-PERF-003 (at least 10 cases open at once):** create 10 cases at once and run J1 and J2 concurrently; check in the audit log that every entry carries its own case ID and no case's data appears in another.
- **NFR-PERF-004 (usage cap):** with `MODEL_USAGE_CAP_PER_RUN` set low, model calls are refused at the cap (TC-004); this is a pytest case, not a timing script.

Rules: start from a clean, reset database; run on an idle machine; state the build, the settings and the hardware in the result; never present a single run as the result. A timing test that is flaky because of the machine is reported with its variance, not retried until it passes.
