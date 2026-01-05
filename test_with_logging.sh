#!/bin/bash

echo "=========================================="
echo "Readable App Test with Logging Enabled"
echo "=========================================="
echo ""

# Copy test document to clipboard
echo "Step 1: Copying test_text.md to clipboard..."
cat test_text.md | pbcopy
echo "✅ Document copied (44KB, 66 chunks)"
echo ""

# Show where logs will be stored
LOG_DIR="$HOME/.readable/logs"
mkdir -p "$LOG_DIR"
echo "Step 2: Logs will be written to:"
echo "   $LOG_DIR"
echo ""

echo "Step 3: Launching app..."
echo ""
echo "🔍 To view logs while app is running:"
echo "   In another terminal, run:"
echo "   ./view_logs.sh tail"
echo ""
echo "📖 App Instructions:"
echo "   1. Click 􀋃 icon in menu bar"
echo "   2. Select '􀈕 Read Clipboard (⌘R)'"
echo "   3. Watch status: 􀆺→􀍟→􀊄"
echo ""
echo "⚠️  If app freezes or crashes:"
echo "   Run: ./view_logs.sh errors"
echo "   This will show what went wrong"
echo ""
echo "Press Enter to launch app..."
read

uv run readable
