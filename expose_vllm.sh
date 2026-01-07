#!/bin/bash
# Expose local vLLM server to the internet using ngrok

echo "======================================"
echo "Exposing vLLM Server via ngrok"
echo "======================================"

# Check if ngrok is available
if ! command -v ./ngrok &> /dev/null; then
    echo "Error: ngrok not found in current directory"
    echo "Please download ngrok from https://ngrok.com/"
    exit 1
fi

# Check if vLLM is running
if ! curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
    echo "Error: vLLM is not running on port 8000"
    echo "Please start vLLM first"
    exit 1
fi

echo "✓ vLLM is running on port 8000"
echo ""
echo "Starting ngrok tunnel..."
echo "This will create a public URL for your vLLM server"
echo ""

# Kill existing ngrok on port 8000
pkill -f "ngrok.*8000" 2>/dev/null

# Start ngrok
./ngrok http 8000 --log=stdout

# The URL will be shown in the ngrok dashboard at http://localhost:4040
