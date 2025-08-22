@echo off
REM ---------------------------
REM Windows Startup Script
REM ---------------------------

echo Checking for Python and pip...

where python >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo Python is required but not installed. Please install Python.
    exit /b 1
)

where pip >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo pip is required but not installed. Please install pip.
    exit /b 1
)

echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

echo Starting chatbot.py...
start "" python chatbot.py

echo Starting FastAPI app on port 9000...
start "" uvicorn mcp_tools:app --reload --port 9000