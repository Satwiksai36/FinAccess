# Benchmark Report: Financial Risk Scoring System

## 1. System Overview
This report documents the performance evaluation of the High-Performance Financial Risk Scoring backend. 
The system features a **FastAPI** web framework natively supporting async operations backed by **PostgreSQL (asyncpg)**, a memory-bound **Redis** caching abstraction, and a togglable **ThreadPoolExecutor** meant to prevent event-loop blockage during heavy CPU-bound Machine Learning inference workloads.

## 2. Concurrency Architecture
- **Web Server:** Uvicorn running on Python 3.11
- **Database:** PostgreSQL 15 connected via pooled `asyncpg` sessions.
- **Cache Layer:** Redis 7 with a 300s TTL per identical prediction payload.
- **Inference Engine:** A dynamically sized `ThreadPoolExecutor` (Allocated $2 \times \text{CPU Cores}$) isolating the static blocking ML mock algorithm (`10,000,000` iteration simulation).
- **Toggle State:** Defined via `INFERENCE_MODE` as either `single` (blocking the main asyncio loop) or `threaded` (offloaded).

## 3. Test Environment & Hardware Specs
*To be filled by the executing engineer:*
- **Host OS:** OS Name / Platform
- **CPU:** Logical Cores available 
- **RAM:** Total System Memory Available
- **Docker Resources:** e.g., Uncapped or restricted via `--cpus=4`

---

## 4. Benchmark Automation Execution Guide

To reproduce these metrics locally, rely on the bundled Locust script `load_testing/locustfile.py`. 

### A. Pre-requisites & Setup
1. Boot the environment utilizing Docker compose. Ensure Redis and Postgres are responsive:
   ```bash
   docker-compose up --build -d
   ```
2. Verify system readiness globally via the health endpoints:
   ```bash
   curl -X GET http://localhost:8000/readiness
   ```
3. Boot the Locust web interface on your host machine:
   ```bash
   # Navigate to the backend directory first
   locust -f load_testing/locustfile.py --host http://localhost:8000
   ```
   *Navigate to `http://localhost:8089` to control user spawn rates natively.*

### B. Validating System Telemetry (Docker Stats)
During execution, monitor resource limitations to verify ThreadPool usage scaling across cores:
```bash
docker stats
```
You should observe CPU utilization comfortably exceeding `100%` solely during `threaded` modes whereas `single` mode execution arbitrarily hard-caps near `100%` (1 core) stalling the FastAPI HTTP pipeline. Check application logs tracking `/metrics` exposed values.

---

## 5. Test Scenarios and Benchmark Tables

Capture values directly from the Locust UI "Statistics" tab and the application `GET /metrics` endpoint after 60-second intervals per mode.

### Scenario A: Single Thread Mode
**Environment Setup:** `INFERENCE_MODE=single`
*Hypothesis:* Because the ML loop is inherently blocking, the event loop will stall. 100 concurrent requests should create severe queuing limits natively degrading the Average and P95 latency profiles geometrically alongside high RPS failures.

| Mode | Users | Duration | Avg (ms) | P95 (ms) | RPS | Fail % |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Single | 10 | 60s | [TBD] | [TBD] | [TBD] | [TBD] |
| Single | 50 | 60s | [TBD] | [TBD] | [TBD] | [TBD] |
| Single | 100 | 60s | [TBD] | [TBD] | [TBD] | [TBD] |

### Scenario B: Threaded Mode
**Environment Setup:** `INFERENCE_MODE=threaded`
*Hypothesis:* Offloading to the ThreadPool executor unlocks parallel CPU cores avoiding FastAPIs asyncio blocking limitations. P95 latency should remain significantly more stable under 100 users bounds while scaling throughput linearly into multi-core overheads.

| Mode | Users | Duration | Avg (ms) | P95 (ms) | RPS | Fail % |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Threaded| 10 | 60s | [TBD] | [TBD] | [TBD] | [TBD] |
| Threaded| 50 | 60s | [TBD] | [TBD] | [TBD] | [TBD] |
| Threaded| 100 | 60s | [TBD] | [TBD] | [TBD] | [TBD] |

### Scenario C: Cache Warm Mode
**Evaluation Focus:** Verifying Redis interception impact on prediction loops.
*Hypothesis:* Repeating identical `/predict/1` payloads reduces execution strictly to I/O fetching speeds instead of ML computation. Drops latencies natively to `< 10ms`.
- **Cache Hit Rate:** [TBD]%
- **Avg Latency (Warm):** [TBD]ms

---

## 6. Observations & Bottleneck Analysis

### 6.1 Stability under 100 Users
*Document standard system stability, observed timeout limits, and Memory leak conditions if evaluated over lengthy 15m intervals here.*

### 6.2 The Multithreading Impact
*Why does the ThreadPool improve performance?* FastAPIs async architecture handles thousands of I/O operations simultaneously (e.g. Database queries), however, pure math computation blocks the thread processing the event loop. Moving the CPU-bound ML mock function out of the event loop utilizing `loop.run_in_executor()` prevents concurrent web requests from stalling, directly accelerating latency limits up to Hardware logical core bounds.

### 6.3 Redis Integration Result
*Why does Redis reduce latency?* Completely bypassing the simulated 10 million mathematical iterations replacing it with instantaneous key-value RAM retrievals reduces processing overheads. 

---

## 7. Conclusion & Optimization Decisions
*Summarize final architectural outcomes, required infrastructural scaling decisions, and validation approvals per environment parameters observed.*

### 7.1 Performance Optimization Decisions Implemented
To harden the system from the initial benchmark targets into a production-grade backend scaling reliably up to 100+ concurrent clients, several manual optimizations were actively enforced reducing resource degradation:
- **ThreadPool Tuning (`THREADPOOL_WORKERS`):** The thread pool dynamically parses `"auto"` falling back gracefully safely to integers. This decouples worker assignment directly allowing operators to configure threading limits manually via Environment variables overriding the default $2 \times \text{CPU}$.
- **Uvicorn Web Workers (`UVICORN_WORKERS`):** Uvicorn now implements explicit `--workers 2`, utilizing the underlying asynchronous `uvloop` C-extensions and `httptools` natively deployed inside a `python:3.11-slim` non-root hardened Docker container.
- **Database Connection Pooling (`DB_POOL_SIZE`):** Asyncpg connections now pre-warm strictly sized pools. `pool_size=10` handles standard I/O streams with an overflow bounded to `max_overflow=20` eliminating stale socket timeout cascades using aggressive `pool_pre_ping`.
- **Redis TTL & Socket Control (`CACHE_TTL`):** Time-To-Live logic parses configurations. Aggressive `socket_timeouts=5s` are deployed enforcing fail-fast caching if Redis instances block.
- **Logging Throttling (`LOG_LEVEL`):** Console overhead during HTTP load testing is mitigated natively by shifting the baseline application structure globally to `WARNING`.
- **Metrics Complexity Mitigation:** Fixed an algorithmic `O(N log N)` computational bottleneck natively caused by real-time latency history sorting preventing `GET /metrics` dumps from pausing internal system threads.
