#!/bin/bash
# KFUPM Course Advisor - Server Startup Script
# This script starts the FastAPI server that serves both the frontend and API

cd "$(dirname "$0")"

echo "======================================"
echo "KFUPM Course Advisor - Starting Server"
echo "======================================"

# Check if vLLM is running on port 8000
echo "Checking vLLM server..."
if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
    echo "✓ vLLM is running on port 8000"
else
    echo "✗ WARNING: vLLM is not responding on port 8000"
    echo "  Please start vLLM first before running this server"
    exit 1
fi

# Clear Python cache to avoid import errors
echo "Clearing Python cache..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
echo "✓ Cache cleared"

# Kill any existing uvicorn process on port 5001
echo "Checking for existing server on port 5001..."
pkill -f "uvicorn.*5001" 2>/dev/null || true
sleep 1

# Start the server
echo "======================================"
echo "Starting FastAPI server on port 5001..."
echo "======================================"
echo ""
echo "Access the app at: http://localhost:5001"
echo "API docs at: http://localhost:5001/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 -m uvicorn api.index:app --host 0.0.0.0 --port 5001 --reload
