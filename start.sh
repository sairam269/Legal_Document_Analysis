#!/bin/bash

# ---------------------------
# Linux Startup Script
# ---------------------------

echo "Checking for Python and pip..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Python3 is required but not installed. Please install Python3."
    exit 1
fi

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo "pip is required but not installed. Please install pip."
    exit 1
fi

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip3 install -r requirements.txt

# Run chatbot.py in background
echo "Starting chatbot.py..."
python3 chatbot.py &

# Run FastAPI app
echo "Starting FastAPI app on port 9000..."
uvicorn mcp_tools:app --reload --port 9000