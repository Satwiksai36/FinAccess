"""
generate_sync_baseline.py — Programmatic single-thread baseline generator
=========================================================================
Runs the server in single-worker mode and executes Locust headless for
10, 50, and 100 concurrent users. Saves results_sync_XX_stats.csv files
that validate the async ThreadPool speedup claims.

Usage (from the backend directory):
    python generate_sync_baseline.py

Requirements:
    pip install locust fastapi uvicorn sqlalchemy aiosqlite python-multipart

What this script does:
1. Starts server.py in a subprocess with THREADPOOL_WORKERS=1
2. Waits for the server to be ready (health check)
3. Runs locust headless for 10, 50, 100 users (60s each)
4. Saves CSV output to results_sync_10_stats.csv etc.
5. Shuts down the server
"""

import subprocess
import sys
import time
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def wait_for_server(url: str, timeout: int = 30) -> bool:
    """Poll the health endpoint until the server is ready."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def run_locust(users: int, spawn_rate: int, csv_prefix: str):
    """Run locust headless for the given concurrency level."""
    cmd = [
        sys.executable, "-m", "locust",
        "-f", os.path.join(HERE, "load_testing", "locustfile_sync.py"),
        "--headless",
        f"-u", str(users),
        f"-r", str(spawn_rate),
        "-t", "60s",
        "--host", "http://localhost:8000",
        f"--csv={csv_prefix}",
    ]
    print(f"\n[Locust] Running: {users} users for 60s  →  {csv_prefix}_stats.csv")
    result = subprocess.run(cmd, cwd=HERE)
    if result.returncode != 0:
        print(f"[WARN] Locust exited with code {result.returncode}")


def main():
    env = os.environ.copy()
    env["THREADPOOL_WORKERS"] = "1"  # Force single-worker mode

    print("=" * 60)
    print("  FinAccess — Single-Thread Baseline Generator")
    print("  Starting server with THREADPOOL_WORKERS=1 ...")
    print("=" * 60)

    # Start server
    server_proc = subprocess.Popen(
        [sys.executable, "server.py"],
        cwd=HERE,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait for ready
    if not wait_for_server("http://localhost:8000/health"):
        print("[ERROR] Server did not start within 30s. Aborting.")
        server_proc.terminate()
        sys.exit(1)

    print("[OK] Server ready on http://localhost:8000")

    try:
        run_locust(users=10,  spawn_rate=2,  csv_prefix="results_sync_10")
        run_locust(users=50,  spawn_rate=5,  csv_prefix="results_sync_50")
        run_locust(users=100, spawn_rate=10, csv_prefix="results_sync_100")
    finally:
        server_proc.terminate()
        server_proc.wait()
        print("\n[OK] Server stopped.")

    print("\n" + "=" * 60)
    print("  Sync baseline CSVs written:")
    for n in [10, 50, 100]:
        path = os.path.join(HERE, f"results_sync_{n}_stats.csv")
        exists = "✓" if os.path.exists(path) else "✗"
        print(f"    {exists} results_sync_{n}_stats.csv")
    print("\n  Compare 'Predict P95' column against results_XX_stats.csv")
    print("  to validate the async ThreadPool speedup numbers.")
    print("=" * 60)


if __name__ == "__main__":
    main()
