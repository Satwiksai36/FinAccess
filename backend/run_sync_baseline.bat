@echo off
REM ============================================================
REM run_sync_baseline.bat — Generate single-thread baseline CSVs
REM ============================================================
REM Run this from the backend\ directory with the server already
REM running in single-worker mode (THREADPOOL_WORKERS=1).
REM
REM Step 1: Open another terminal and start the server with 1 worker:
REM     set THREADPOOL_WORKERS=1
REM     python server.py
REM
REM Step 2: Run this script:
REM     run_sync_baseline.bat
REM
REM Output: results_sync_10_stats.csv, results_sync_50_stats.csv, results_sync_100_stats.csv
REM These are the single-thread baseline CSVs.  Compare against results_XX_stats.csv
REM (generated with the default multi-worker pool) to validate the speedup claims.
REM ============================================================

echo [1/3] Running sync baseline: 10 concurrent users...
python -m locust -f load_testing/locustfile_sync.py --headless -u 10 -r 2 -t 60s --host http://localhost:8000 --csv=results_sync_10
if errorlevel 1 goto :error

echo [2/3] Running sync baseline: 50 concurrent users...
python -m locust -f load_testing/locustfile_sync.py --headless -u 50 -r 5 -t 60s --host http://localhost:8000 --csv=results_sync_50
if errorlevel 1 goto :error

echo [3/3] Running sync baseline: 100 concurrent users...
python -m locust -f load_testing/locustfile_sync.py --headless -u 100 -r 10 -t 60s --host http://localhost:8000 --csv=results_sync_100
if errorlevel 1 goto :error

echo.
echo ============================================================
echo  DONE. Sync baseline CSVs written:
echo    results_sync_10_stats.csv
echo    results_sync_50_stats.csv
echo    results_sync_100_stats.csv
echo.
echo  Compare predict P95 against results_10_stats.csv etc.
echo  to validate the async ThreadPool speedup numbers.
echo ============================================================
goto :eof

:error
echo.
echo ERROR: Locust run failed. Make sure:
echo   1. server.py is running (python server.py)
echo   2. THREADPOOL_WORKERS=1 is set in the server terminal
echo   3. locust is installed (pip install locust)
exit /b 1
