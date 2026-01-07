#!/bin/bash
# Stop KFUPM Course Advisor server

echo "Stopping KFUPM Course Advisor server..."
pkill -f "uvicorn.*api.index.*5001"

if [ $? -eq 0 ]; then
    echo "✓ Server stopped"
else
    echo "✗ No server found running on port 5001"
fi
