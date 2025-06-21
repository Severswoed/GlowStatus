#!/bin/bash

# GlowStatus Setup Script

echo "🚀 Starting GlowStatus setup..."

# Check for .env
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "➡️  Please create one using .env.example before continuing."
    exit 1
fi

# Check required env vars
echo "🔍 Validating environment variables..."
REQUIRED_VARS=(GOVEE_API_KEY GOVEE_DEVICE_ID)

for VAR in "${REQUIRED_VARS[@]}"; do
    if ! grep -q "$VAR=" .env; then
        echo "❌ Missing $VAR in .env"
        MISSING=true
    fi
done

if [ "$MISSING" = true ]; then
    echo "⚠️  One or more required environment variables are missing."
    exit 1
else
    echo "✅ Environment variables look good."
fi

# Create Python venv if not exists
if [ ! -d "venv" ]; then
    echo "🐍 Setting up Python virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install Python dependencies
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "⚠️  No requirements.txt found. Skipping Python package install."
fi

# Install Node dependencies if package.json exists
if [ -f "package.json" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

echo "🎉 GlowStatus setup complete. You can now run the application."