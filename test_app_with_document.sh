#!/bin/bash

echo "=================================="
echo "Testing Readable with test_text.md"
echo "=================================="
echo ""
echo "Step 1: Copying test document to clipboard..."
cat test_text.md | pbcopy
echo "✅ Document copied (44KB, 6799 words, 66 chunks)"
echo ""
echo "Step 2: Launching Readable app..."
echo ""
echo "The app should appear in your menu bar with 􀋃 icon"
echo ""
echo "Next steps in the app:"
echo "  1. Click the 􀋃 icon in menu bar"
echo "  2. Select '􀈕 Read Clipboard (⌘R)'"
echo "  3. Watch status change: 􀆺→􀍟→􀊄"
echo "  4. Audio will play for ~62 minutes!"
echo ""
echo "Launching app now..."
echo ""

uv run readable
