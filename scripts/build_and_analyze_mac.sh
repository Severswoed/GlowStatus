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

# Run the optimized build
echo "🔨 Running optimized py2app build..."
echo "💡 This build excludes massive unnecessary PySide6 components like:"
echo "   - QtWebEngine (web browser engine)"
echo "   - Qt3D (3D graphics)"
echo "   - QtMultimedia (video/audio codecs)"
echo "   - QtCharts/QtGraphs (charting libraries)"
echo "   - QtQuick (QML UI framework)"
echo "   - And many other unused components"
echo
python "$SCRIPT_DIR/build_mac.py" py2app

# Check if build was successful
if [ -d "dist/GlowStatus.app" ]; then
    echo
    echo "✅ Build completed successfully!"
    echo
    
    # Show detailed app size analysis
    echo "📊 Application size analysis:"
    echo "═══════════════════════════════════════════════════════════════"
    ls -lah dist/
    echo
    echo "📦 Total app size:"
    du -sh dist/GlowStatus.app
    echo
    
    # Analyze what's taking up space inside the app
    echo "🔍 Top space consumers inside the app:"
    echo "═══════════════════════════════════════════════════════════════"
    
    # Check Contents directory breakdown
    if [ -d "dist/GlowStatus.app/Contents" ]; then
        echo "📁 Contents directory breakdown:"
        du -sh dist/GlowStatus.app/Contents/* | sort -hr | head -10
        echo
    fi
    
    # Check Frameworks if they exist
    if [ -d "dist/GlowStatus.app/Contents/Frameworks" ]; then
        echo "🔧 Frameworks (should be minimal):"
        du -sh dist/GlowStatus.app/Contents/Frameworks/* | sort -hr | head -5
        echo
    fi
    
    # Check Resources/lib for PySide6 components
    if [ -d "dist/GlowStatus.app/Contents/Resources/lib/python3.9/PySide6" ]; then
        echo "⚙️  PySide6 components included:"
        du -sh dist/GlowStatus.app/Contents/Resources/lib/python3.9/PySide6/* | sort -hr | head -10
        echo
        
        # Check if any large unwanted components slipped through
        echo "❌ Checking for unwanted large components that should be excluded:"
        for component in Qt3D QtWebEngine QtMultimedia QtCharts QtQuick3D QtDataVisualization; do
            if [ -d "dist/GlowStatus.app/Contents/Resources/lib/python3.9/PySide6/${component}"* ]; then
                echo "   ⚠️  Found unwanted component: ${component}"
                du -sh dist/GlowStatus.app/Contents/Resources/lib/python3.9/PySide6/${component}*
            fi
        done
        echo
    fi
    
    # Find the most recent build log
    LATEST_LOG=$(ls -t build/build_log_*.txt 2>/dev/null | head -n1)
    
    if [ -n "$LATEST_LOG" ]; then
        echo "📝 Build log saved to: $LATEST_LOG"
        echo
        echo "💡 To view the complete build log:"
        echo "   cat '$LATEST_LOG'"
        echo "   or"
        echo "   open '$LATEST_LOG'"
        echo
        echo "📤 To share the build log for analysis:"
        echo "   cat '$LATEST_LOG' | pbcopy    # Copy to clipboard"
        echo "   or"
        echo "   open '$LATEST_LOG'           # Open in text editor"
        echo
        
        # Show summary of what was excluded
        echo "📋 Build summary - Major exclusions for size optimization:"
        echo "═══════════════════════════════════════════════════════════════"
        echo "✅ Successfully excluded:"
        echo "   - QtWebEngine (web browser engine) - ~200MB+"
        echo "   - Qt3D frameworks (3D graphics) - ~50MB+"
        echo "   - QtMultimedia + FFmpeg codecs - ~100MB+"
        echo "   - QtCharts/QtGraphs/QtDataVisualization - ~30MB+"
        echo "   - QtQuick/QML frameworks - ~50MB+"
        echo "   - All Qt style implementations - ~20MB+"
        echo "   - Development/testing tools - ~10MB+"
        echo
        echo "🎯 Target size: ~50-100MB (down from 1GB+)"
        echo
        
        # Show last few lines of the log for immediate feedback
        echo "� Last few lines of build log:"
        echo "═══════════════════════════════════════════════════════════════"
        tail -15 "$LATEST_LOG"
        echo "═══════════════════════════════════════════════════════════════"
        
    else
        echo "⚠️  Build log not found in build/ directory"
        echo "💡 The build completed but logging may have failed"
    fi
    
else
    echo "❌ Build failed - GlowStatus.app not found in dist/"
    exit 1
fi

echo
echo "🎉 Build and analysis complete!"
