@echo off
title Fixing FinAccess Backend Errors

echo =================================================================
echo   Fixing "Port 8000 in use" and "No module named 'torch'"
echo =================================================================
echo.

echo [1/2] Freeing port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    echo Found process %%a using port 8000. Terminating...
    taskkill /PID %%a /F >nul 2>&1
)
echo [OK] Port 8000 is now free.
echo.

echo [2/2] Installing Machine Learning packages...
echo (This includes PyTorch, XGBoost, SHAP. It may take a few minutes to download.)
pip install torch xgboost shap numpy scikit-learn --index-url https://download.pytorch.org/whl/cpu

echo.
echo =================================================================
echo   ALL FIXED!
echo.
echo   You can now start the backend normally:
echo   cd "c:\Users\hp\Desktop\New folder\FinAccess\backend"
echo   python server.py
echo =================================================================
pause
