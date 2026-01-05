#!/bin/bash

echo "Testing app launch..."
echo ""

# Try to launch for 3 seconds
timeout 3 uv run readable 2>&1 || true

echo ""
echo "Checking latest log for errors..."
sleep 1

# Find newest log
LATEST_LOG=$(ls -t ~/.readable/logs/*.log 2>/dev/null | head -1)

if [ -n "$LATEST_LOG" ]; then
    echo "Latest log: $LATEST_LOG"
    echo ""
    echo "=== Last 30 lines ==="
    tail -30 "$LATEST_LOG"
    echo ""
    echo "=== Errors/Warnings ==="
    grep -E "ERROR|WARNING" "$LATEST_LOG" || echo "No errors found"
else
    echo "No log file found"
fi
