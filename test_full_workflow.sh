#!/bin/bash

echo "=========================================="
echo "Full Document Test - test_text.md"
echo "=========================================="
echo ""
echo "📄 Document: 44KB, 6,799 words, 66 chunks"
echo "⏱️  Estimated: ~25s to generate, ~62 min to play"
echo ""
echo "Copying to clipboard..."
cat test_text.md | pbcopy
echo "✅ Document copied!"
echo ""
echo "📝 Next steps:"
echo "   1. Launch: uv run readable"
echo "   2. Click 􀋃 in menu bar"
echo "   3. Click '􀈕 Read Clipboard' (or press ⌘R)"
echo "   4. Watch: 􀆺→􀍟→􀊄 (Idle→Processing→Playing)"
echo "   5. Listen to your 62-minute document!"
echo ""
echo "🎧 Controls while playing:"
echo "   ⌘P - Play/Resume"
echo "   ⌘K - Pause"
echo "   ⌘→ - Skip to next chunk"
echo ""
echo "Press Enter to launch app..."
read

uv run readable
