"""
locustfile_sync.py — Single-Thread (Sequential) Baseline Load Test
===================================================================
Run this with INFERENCE_MODE=direct (or the standalone server.py in single-thread mode)
to produce the single-thread baseline CSV that justifies the multi-vs-sync speedup numbers.

Usage (from the backend directory):
    # Terminal 1: start server in synchronous mode
    set INFERENCE_MODE=direct
    python server.py

    # Terminal 2: run the sync baseline locust test
    python -m locust -f load_testing/locustfile_sync.py --headless -u 10  -r 2  -t 60s --host http://localhost:8000 --csv=results_sync_10
    python -m locust -f load_testing/locustfile_sync.py --headless -u 50  -r 5  -t 60s --host http://localhost:8000 --csv=results_sync_50
    python -m locust -f load_testing/locustfile_sync.py --headless -u 100 -r 10 -t 60s --host http://localhost:8000 --csv=results_sync_100

Note
----
server.py always uses ThreadPoolExecutor internally (no INFERENCE_MODE switch in the demo server).
To get a true single-thread baseline, either:
  a) Use app/main.py with INFERENCE_MODE=direct (disables run_in_executor), OR
  b) Limit the ThreadPoolExecutor to max_workers=1 via:
         set THREADPOOL_WORKERS=1
     This forces all ML calls to queue through a single worker thread,
     simulating a blocking synchronous execution model.

The results are saved as results_sync_XX_stats.csv for comparison against
the async ThreadPool runs in results_XX_stats.csv.
"""

import random
from locust import HttpUser, task, between


class SyncBaselineUser(HttpUser):
    """
    Identical request pattern to locustfile.py but labelled as sync-baseline.
    The "sync" behaviour is server-side (THREADPOOL_WORKERS=1), not client-side.
    Client wait_time is kept identical to ensure fair throughput comparison.
    """

    wait_time = between(1.0, 3.0)

    def on_start(self):
        """Register + login once per virtual user to acquire a JWT token."""
        self.user_email = f"synctest_{random.randint(100000, 9999999)}@test.com"
        self.password = "secure_password"

        self.client.post(
            "/auth/register",
            json={"email": self.user_email, "password": self.password, "role": "APPLICANT"},
            name="[Sync] Register User",
        )

        response = self.client.post(
            "/auth/login",
            data={"username": self.user_email, "password": self.password},
            name="[Sync] Login JWT",
        )

        if response.status_code == 200:
            self.headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        else:
            response.failure(f"Failed to acquire JWT. Status: {response.status_code}")
            self.environment.runner.quit()

    @task
    def execute_risk_prediction_sync(self):
        """
        Same predict endpoint as the async test.
        Server-side worker pool is limited to 1 thread (THREADPOOL_WORKERS=1)
        to simulate synchronous / single-thread execution.
        """
        applicant_id = random.randint(1, 20)

        with self.client.post(
            f"/predict/{applicant_id}",
            headers=getattr(self, "headers", {}),
            catch_response=True,
            name="[Sync] Predict - Single Worker ML Target",
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.failure("404 — applicant not found")
            else:
                response.failure(f"HTTP {response.status_code}")
