#!/bin/bash
# Start KFUPM Course Advisor in background

cd "$(dirname "$0")"

echo "Starting KFUPM Course Advisor in background..."

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Kill existing process
pkill -f "uvicorn.*api.index.*5001" 2>/dev/null || true
sleep 1

# Start in background
nohup python3 -m uvicorn api.index:app --host 0.0.0.0 --port 5001 --reload > server.log 2>&1 &

PID=$!
echo "✓ Server started with PID: $PID"
echo "✓ Logs: tail -f server.log"
echo "✓ Access at: http://localhost:5001"
echo ""
echo "To stop: ./stop_server.sh"
