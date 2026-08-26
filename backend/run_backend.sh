#!/bin/bash

# Navigate to the backend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Detect and activate virtual environment if present
if [ -d "venv_mac" ] && [ -f "venv_mac/bin/activate" ]; then
    echo "Activating virtual environment (venv_mac)..."
    source venv_mac/bin/activate
elif [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment (venv)..."
    source venv/bin/activate
elif [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
    echo "Activating virtual environment (.venv)..."
    source .venv/bin/activate
elif [ -d "venv/Scripts" ] && [ -f "venv/Scripts/activate" ]; then
    echo "Activating Windows virtual environment (venv)..."
    source venv/Scripts/activate
else
    echo "No virtual environment found. Running with system Python/uvicorn..."
fi

# Run the FastAPI server with uvicorn
echo "Starting backend server on http://127.0.0.1:8000..."
uvicorn main:app --reload --host 127.0.0.1 --port 8000
