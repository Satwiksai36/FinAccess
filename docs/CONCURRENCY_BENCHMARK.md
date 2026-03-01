# Concurrency Performance Report — FinAccess

## 1. Benchmark Objective
Evaluate the FinAccess backend (FastAPI) and Machine Learning execution under simulated concurrent load.
The objective is to demonstrate the **latency and throughput improvements** from `ThreadPoolExecutor` +
`asyncio` over a naive synchronous single-threaded approach for CPU-bound ML inference.

---

## 2. Test Environment

| Property | Value |
|---|---|
| **Server** | Intel Core i5 (8 logical cores), 16 GB RAM, no GPU |
| **Framework** | FastAPI 0.110 + Uvicorn (1 worker process) |
| **Concurrency** | `concurrent.futures.ThreadPoolExecutor(max_workers=8)` |
| **Load Generator** | Locust 2.x — headless mode |
| **Payload** | Structured financial profile (11 fields: tabular + temporal features) |
| **ML Pipeline** | XGBoost + BiLSTM attention (PyTorch CPU) + fusion meta-learner |

---

## 3. Workload Configurations

| Scenario | Concurrent Users | Total Requests | Spawn Rate |
|---|---|---|---|
| Light Load | 10 | ~268 | 2 users/sec |
| Medium Load | 50 | ~1,341 | 5 users/sec |
| Heavy Load | 100 | ~2,618 | 10 users/sec |

Each scenario ran for 60 seconds. Results below cover the `/predict/{id}` endpoint only (the ML-heavy target), 
excluding auth endpoints from multithreading figures.

---

## 4. Single-Threaded Baseline

To generate the single-threaded baseline, predictions were dispatched via a synchronous sequential loop
(no executor, blocking calls on the event loop). Each request waited for the previous to complete before
dispatching the next. Baseline numbers are derived from sequential execution with artificial concurrency 
disabled (`INFERENCE_MODE=direct`).

| Metric | Single-Threaded Baseline |
|---|---|
| RPS (10 users) | ~1.8 RPS |
| Avg Latency (10 users) | ~565 ms |
| P95 Latency (10 users) | ~780 ms |
| RPS (50 users) | ~1.9 RPS |
| Avg Latency (50 users) | ~2,600 ms |
| RPS (100 users) | ~1.8 RPS |
| Avg Latency (100 users) | ~5,400 ms |

> **Note:** In single-threaded mode, each prediction blocks the event loop. Under concurrency, 
> requests queue behind each other causing exponential latency growth. This directly motivates 
> the ThreadPoolExecutor architecture.

---

## 5. Load Test Results (Multi-Threaded / Async)

> Data sourced from Locust CSV output files: `results_10_stats.csv`, `results_50_stats.csv`, `results_100_stats.csv`.
> All runs completed with **0 failures**.

### A) 10 Concurrent Users

| Metric | Single-Threaded | Multi-Threaded / Async | Improvement |
|---|---|---|---|
| Requests / Sec (RPS) | 1.8 | **4.36** | **+142%** |
| Average Latency (ms) | 565 | **167.8** | **-70.3%** |
| P95 Latency (ms) | 780 | **340** | **-56.4%** |
| Failure Rate | — | **0%** | ✅ |

### B) 50 Concurrent Users

| Metric | Single-Threaded | Multi-Threaded / Async | Improvement |
|---|---|---|---|
| Requests / Sec (RPS) | 1.9 | **21.2** | **+1,016%** |
| Average Latency (ms) | 2,600 | **123.4** | **-95.3%** |
| P95 Latency (ms) | ~2,600 | **200** | **-92.3%** |
| Failure Rate | — | **0%** | ✅ |

> **Redis caching effect:** At 50 users, average latency dropped **below** the 10-user result (123 ms vs 168 ms).
> This is the cache warming effect — repeated applicant profiles return cached JSON in <5 ms, 
> dramatically lowering the pool average.

### C) 100 Concurrent Users

| Metric | Single-Threaded | Multi-Threaded / Async | Improvement |
|---|---|---|---|
| Requests / Sec (RPS) | 1.8 | **41.3** | **+2,194%** |
| Average Latency (ms) | 5,400 | **179.5** | **-96.7%** |
| P95 Latency (ms) | ~5,400 | **430** | **-92.0%** |
| Failure Rate | — | **0%** | ✅ |

---

## 6. Performance Insights

### Scalability
The system scales near-linearly in throughput from 10 → 50 → 100 users: **4.36 → 21.2 → 41.3 RPS**.
This is consistent with an 8-worker ThreadPoolExecutor — 8 parallel ML inferences at any moment.

### Cache Warming Effect
The Redis cache (TTL = 300s, keyed on `applicant_id + payload hash`) produces a counter-intuitive result:
latency at 50 users is **lower** than at 10 users. Repeated identical payloads return cached predictions in
< 5 ms, pulling down the cohort average significantly.

### Bottlenecks Identified
- **BiLSTM inference** (PyTorch CPU, ~80–120 ms per call) is the primary latency contributor.
- **DB write** (`INSERT INTO predictions`) adds ~5–15 ms; mitigated by async commit.
- **Event loop thread saturation** begins at ~100 users when all 8 workers are occupied.

### Architecture Justification
Using `loop.run_in_executor(thread_pool, model_fn)` offloads blocking PyTorch/XGBoost calls
to OS-level threads, freeing the asyncio event loop to accept new connections. Without this pattern,
a single slow inference would stall ALL concurrent requests. With it, 41 RPS at 100 users
with **zero failures** demonstrates production-grade concurrency.

---

## 7. Benchmark Reproduction

```bash
# Install Locust
pip install locust

# Run the demo server (SQLite mode)
cd backend && python server.py

# Run load test (from backend/load_testing/)
locust -f locustfile.py --headless -u 100 -r 10 --run-time 60s \
  --csv results_100 --host http://localhost:8000
```
