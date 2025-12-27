#!/bin/bash

# LLM Council - Start script

echo "Starting LLM Council..."
echo ""

# Start backend
if [ -f "certs/cert.pem" ] && [ -f "certs/key.pem" ]; then
    echo "Starting backend on https://0.0.0.0:8001 (SSL enabled)..."
    uv run python -m backend.main --ssl-keyfile=certs/key.pem --ssl-certfile=certs/cert.pem &
else
    echo "Starting backend on http://0.0.0.0:8001 (No SSL)..."
    uv run python -m backend.main &
fi
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 2

# Start frontend
echo "Starting frontend..."
cd frontend
if [ "$1" == "--host" ]; then
    echo "  Mode: Remote Access (Host: 0.0.0.0)"
    npm run dev -- --host &
else
    echo "  Mode: Localhost"
    npm run dev &
fi
FRONTEND_PID=$!

echo ""
echo "✓ LLM Council is running!"
echo "  Backend:  https://0.0.0.0:8001"
echo "  Frontend: https://localhost:5173"
echo ""
echo "Note: Accept the self-signed certificate warning in your browser."
echo "Press Ctrl+C to stop both servers"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
