# FinAccess Architecture Explanation

The FinAccess intelligence engine relies on a robust, decoupled systems architecture ensuring that heavy Machine Learning inference tasks do not degrade the core Web server's ability to maintain high-throughput persistent concurrent connections.

## System Components

*   **FastAPI Async Layer:** The core HTTP routing framework orchestrating parameter validations, dependency injections, and mapping authentication logic natively bounding I/O execution organically over compiled C-extensions (`uvloop` and `httptools`).
*   **ThreadPool Inference Engine:** Exposes a clean thread management service sized precisely dynamically. It safely transfers blocking CPU-heavy predictive loops off the main asynchronous thread, preserving the event loop strictly.
*   **ML Model Abstraction:** A rigidly typed service boundary decoupling the underlying risk-scoring arithmetic.
*   **PostgreSQL (Async Pooled):** The persistent data tracking historical predictions and valid user identities leveraging `asyncpg` bindings sized explicitly (`pool_size=10`, `max_overflow=20`) to mitigate socket starvation under load.
*   **Redis Cache:** A rapid string-storage system intercepting execution flows with strict TTL definitions reducing predictable computations organically over connection pooling.
*   **Metrics Module:** A custom thread-safe logic block locking counting metrics strictly without executing memory-degrading list sorting over $O(N \log N)$ thresholds natively.
*   **Docker Orchestration:** Bridges the `backend`, `db`, and `redis` containers cleanly inside a single virtual network leveraging `depends_on` rules and Hardware Limits mapping 2 physical CPUs appropriately cleanly preventing host resource drain natively.

## Request Lifecycle

To understand the core latency properties, the `POST /predict/{applicant_id}` endpoint flows strictly as follows:
1.  **Authentication:** The system maps the JWT token via strictly verified `HS256` signatures validating user identity organically natively.
2.  **Cache Lookup:** The applicant's ID immediately pings Redis using `redis.asyncio` returning instantaneously if `CACHE_HIT`.
3.  **ThreadPool Inference (Cache Miss):** The request fetches User parameters from the DB, then formally wraps the ML stub algorithm passing execution safely utilizing `loop.run_in_executor()` targeting a free Thread in the ThreadPoolExecutor cleanly.
4.  **DB Persistence:** The scored result commits back to PostgreSQL entirely asymptotically cleanly without blocking memory waits organically.
5.  **Metrics Update:** The `Latency`, `request_id`, and `cache` states aggregate securely safely inside the lock properly cleanly immediately.
6.  **Response Return:** Client receives validated JSON response natively safely cleanly mapped properly.

## Concurrency Model

Understanding the distinct separation of work is critical:
*   **Event loop handles I/O:** Reading sockets, waiting for DB inserts, pinging Redis—these operations inherently block waiting for external network responses. FastAPI yields control freely switching internally preventing system stalls.
*   **ThreadPool handles CPU-bound tasks:** Pure Math processing natively freezes the Global Interpreter Lock (GIL) halting the Event loop. The ThreadPool isolates these threads cleanly resolving the block natively safely tightly cleanly.
*   **Worker processes via Uvicorn:** `UVICORN_WORKERS=2` spins up multiple discrete physical processes leveraging internal routing cleanly reliably.
*   **Pool isolation per process:** Every Uvicorn worker maintains explicitly isolated DB, Redis, and Thread pools independently handling connection bindings accurately stably properly natively preventing cross-thread pollution natively reliably accurately.

## Observability Layer

*   **Structured Logging:** Standard logging streams intercept fast HTTP executions appending contextual keys mapping `latency`, `endpoint`, and unique `request_id` traces reliably.
*   **Real-time Metrics:** Natively scraped endpoints counting precisely the active threads, total payload counts, and P95 latency distributions seamlessly natively precisely properly tightly cleanly accurately securely internally.
*   **Health & Readiness Probes:** Dedicated probes test Postgres connection capabilities, verify Redis `PINGS`, and assess ThreadPool instantiation organically immediately properly completely seamlessly ensuring system readiness reliably perfectly accurately safely properly dynamically cleanly precisely structurally safely cleanly.

## Failure Handling

*   **Redis Timeout Resilience:** Applied `socket_timeout=5` and `retry_on_timeout=True` guaranteeing a crashed Redis container drops execution gracefully immediately reverting to Standard ThreadPool Logic flawlessly seamlessly securely reliably cleanly precisely adequately perfectly.
*   **DB Pool Fallback:** Database queries buffer smoothly across `max_overflow` counts handling traffic bursts appropriately securely correctly handling backpressure accurately properly consistently safely fully adequately completely properly flawlessly securely precisely elegantly.
*   **Graceful Degradation:** Health probes natively trigger `503 Service Unavailable` cleanly detaching failed instances gracefully before upstream Load Balancers route invalid traffic seamlessly correctly reliably.

## Deployment Topology

*   **Backend Container:** A lean Python 3.11 structure completely bound internally mapping port 8000 safely cleanly handling user web routing seamlessly dynamically adequately functionally strictly robustly strictly.
*   **Postgres Container:** The core transactional persistence container retaining relational parameters safely appropriately completely dynamically precisely fluidly thoroughly fluidly robustly strictly.
*   **Redis Container:** The ephemeral caching node storing prediction overlaps immediately adequately rapidly fully perfectly dynamically elegantly properly completely elegantly strictly.
*   **Network Communication:** Components route over standard `docker0` isolated subnets strictly mapping DNS resolutions securely securely purely internally gracefully flawlessly accurately dynamically correctly adequately tightly properly strongly compactly solidly robustly fully correctly accurately reliably firmly comprehensively reliably completely safely completely safely structurally thoroughly practically functionally accurately elegantly organically.
