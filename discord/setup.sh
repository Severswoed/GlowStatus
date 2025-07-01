#!/bin/bash
# Quick setup script for GlowStatus Discord

echo "🤖 Setting up GlowStatus Discord server..."

# Check if bot token is set
if [ -z "$DISCORD_BOT_TOKEN" ]; then
    echo "❌ Please set DISCORD_BOT_TOKEN environment variable"
    echo "   Get your bot token from: https://discord.com/developers/applications"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install discord.py

# Run setup
echo "🚀 Running Discord setup..."
python discord/setup_discord.py

echo "✅ Discord setup complete!"
echo "📋 Next steps:"
echo "   1. Invite bot to your server with Administrator permissions"
echo "   2. Run the setup script"
echo "   3. Configure GitHub webhooks for #dev-updates"
echo "   4. Add server invite link to your README"
