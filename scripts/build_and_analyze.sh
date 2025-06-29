#!/bin/bash

# Build and analyze macOS app script
# This script runs the macOS build and provides easy access to the build log

set -e  # Exit on any error

echo "🚀 Starting GlowStatus macOS build with detailed logging..."
echo "📅 $(date)"
echo

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "📁 Project root: $PROJECT_ROOT"
echo "📁 Script directory: $SCRIPT_DIR"
echo

# Change to project root
cd "$PROJECT_ROOT"

# Clean previous build
echo "🧹 Cleaning previous build artifacts..."
rm -rf build/ dist/
echo

# Run the build
echo "🔨 Running py2app build..."
python "$SCRIPT_DIR/build_mac.py" py2app

# Check if build was successful
if [ -d "dist/GlowStatus.app" ]; then
    echo
    echo "✅ Build completed successfully!"
    echo
    
    # Show app size
    echo "📊 Application size analysis:"
    ls -lah dist/
    echo
    du -sh dist/GlowStatus.app
    echo
    
    # Find the most recent build log
    LATEST_LOG=$(ls -t build/build_log_*.txt 2>/dev/null | head -n1)
    
    if [ -n "$LATEST_LOG" ]; then
        echo "📝 Build log location: $LATEST_LOG"
        echo
        echo "💡 To view the complete build log:"
        echo "   cat '$LATEST_LOG'"
        echo "   or"
        echo "   open '$LATEST_LOG'"
        echo
        echo "📤 To share the build log, copy the contents of:"
        echo "   $LATEST_LOG"
        echo
        
        # Show last few lines of the log for immediate feedback
        echo "📋 Last few lines of build log:"
        echo "═══════════════════════════════════════════════════════════════"
        tail -20 "$LATEST_LOG"
        echo "═══════════════════════════════════════════════════════════════"
        
    else
        echo "⚠️  Build log not found in build/ directory"
    fi
    
else
    echo "❌ Build failed - GlowStatus.app not found in dist/"
    exit 1
fi

echo
echo "🎉 Build and analysis complete!"
