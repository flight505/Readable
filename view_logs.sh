#!/bin/bash

LOG_DIR="$HOME/.readable/logs"

if [ ! -d "$LOG_DIR" ]; then
    echo "No logs directory found at $LOG_DIR"
    exit 1
fi

echo "==================================="
echo "Readable App Logs"
echo "==================================="
echo ""

# Find the most recent log file
LATEST_LOG=$(ls -t "$LOG_DIR"/readable_*.log 2>/dev/null | head -1)

if [ -z "$LATEST_LOG" ]; then
    echo "No log files found"
    exit 1
fi

echo "Latest log file: $LATEST_LOG"
echo ""

if [ "$1" == "tail" ]; then
    echo "Following log in real-time (Ctrl+C to stop)..."
    echo ""
    tail -f "$LATEST_LOG"
elif [ "$1" == "errors" ]; then
    echo "=== ERROR and WARNING lines ==="
    echo ""
    grep -E "ERROR|WARNING" "$LATEST_LOG"
else
    echo "--- Last 50 lines ---"
    echo ""
    tail -50 "$LATEST_LOG"
    echo ""
    echo "Usage:"
    echo "  ./view_logs.sh        - Show last 50 lines"
    echo "  ./view_logs.sh tail   - Follow log in real-time"
    echo "  ./view_logs.sh errors - Show only errors/warnings"
    echo ""
    echo "Full log: $LATEST_LOG"
fi
