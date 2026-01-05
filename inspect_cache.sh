#!/bin/bash

CACHE_DIR="$HOME/.readable/cache"
CACHE_INDEX="$HOME/.readable/cache_index.json"

echo "=========================================="
echo "Readable Cache Inspection"
echo "=========================================="
echo ""

if [ ! -d "$CACHE_DIR" ]; then
    echo "No cache directory found"
    exit 0
fi

echo "📁 Cache Location:"
echo "   $CACHE_DIR"
echo ""

# Count files
FILE_COUNT=$(ls -1 "$CACHE_DIR"/*.wav 2>/dev/null | wc -l | tr -d ' ')
echo "📊 Cache Stats:"
echo "   Files: $FILE_COUNT"

if [ $FILE_COUNT -gt 0 ]; then
    # Total size
    TOTAL_SIZE=$(du -sh "$CACHE_DIR" | cut -f1)
    echo "   Size: $TOTAL_SIZE"
    echo ""
    
    echo "📄 Recent files (last 5):"
    ls -lht "$CACHE_DIR"/*.wav 2>/dev/null | head -5 | awk '{print "   " $9 " - " $5}'
    echo ""
    
    # Pick a random file to test
    RANDOM_FILE=$(ls "$CACHE_DIR"/*.wav 2>/dev/null | head -1)
    if [ -n "$RANDOM_FILE" ]; then
        echo "🎧 Test playback of cached file:"
        echo "   afplay \"$RANDOM_FILE\""
        echo ""
        echo "Press Enter to play sample cached audio..."
        read
        afplay "$RANDOM_FILE"
    fi
fi

if [ -f "$CACHE_INDEX" ]; then
    echo ""
    echo "📋 Cache Index:"
    cat "$CACHE_INDEX" | python3 -m json.tool 2>/dev/null || cat "$CACHE_INDEX"
fi

echo ""
echo "🗑️  To clear cache:"
echo "   rm -rf ~/.readable/cache"
echo "   (or use app menu: '􀈑 Clear Cache')"
