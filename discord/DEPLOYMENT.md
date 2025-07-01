# GlowStatus Discord Bot Deployment Guide

Quick reference for deploying the GlowStatus Discord bot to various hosting platforms.

## 🚨 Important: Why You Need Hosting

**Your Discord bot MUST run 24/7 to work properly.**

When you run `python setup_discord.py` in your terminal:
- ✅ Bot works while terminal is open
- ❌ Bot goes offline when you close terminal
- ❌ Bot goes offline when computer sleeps/shuts down
- ❌ Welcome reactions, admin invites, etc. stop working

## Quick Start Options

### 1. Railway (Easiest - Free Tier)

1. Push your code to GitHub
2. Go to [Railway](https://railway.app)
3. Connect your GitHub repo
4. Set environment variable: `DISCORD_BOT_TOKEN=your_token`
5. Deploy!

**Pros**: Automatic deployments, free tier
**Cons**: Limited free resources

### 2. DigitalOcean Droplet (Most Reliable - $5/month)

```bash
# 1. Create Ubuntu 22.04 droplet ($5/month)
# 2. SSH into your server
ssh root@your_server_ip

# 3. Install dependencies
apt update && apt install python3 python3-pip git

# 4. Clone repo and setup
git clone https://github.com/yourusername/GlowStatus.git
cd GlowStatus
pip3 install -r discord/requirements.txt

# 5. Set environment variable
echo 'export DISCORD_BOT_TOKEN="your_token_here"' >> ~/.bashrc
source ~/.bashrc

# 6. Create systemd service for auto-restart
nano /etc/systemd/system/glowstatus-bot.service
```

Paste this service configuration:
```ini
[Unit]
Description=GlowStatus Discord Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/GlowStatus
Environment=DISCORD_BOT_TOKEN=your_token_here
ExecStart=/usr/bin/python3 discord/setup_discord.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 7. Enable and start
systemctl enable glowstatus-bot
systemctl start glowstatus-bot

# 8. Check status
systemctl status glowstatus-bot
```

### 3. Raspberry Pi (Best Value - $50 one-time)

Perfect for 24/7 home hosting with minimal power usage.

```bash
# 1. Install Raspberry Pi OS
# 2. SSH or open terminal
sudo apt update && sudo apt install python3-pip git

# 3. Clone and setup (same as DigitalOcean above)
git clone https://github.com/yourusername/GlowStatus.git
cd GlowStatus
pip3 install -r discord/requirements.txt

# 4. Use same systemd service setup as DigitalOcean
```

## Environment Variables

All platforms need these environment variables:

```bash
# Required
DISCORD_BOT_TOKEN="your_discord_bot_token"

# Optional
GITHUB_WEBHOOK_URL="your_github_webhook_url"
LOG_LEVEL="INFO"
```

## Testing Your Deployment

1. **Check Bot Status**: Bot should show "Online" in your Discord server
2. **Test Welcome Reaction**: React with 👋 in #welcome channel
3. **Test Admin Commands**: Try `!pending_invites` if you're an admin
4. **Monitor Logs**: Check for any error messages

## Troubleshooting

### Bot Shows as Offline
```bash
# Check if process is running
ps aux | grep python
systemctl status glowstatus-bot

# Check logs for errors
journalctl -u glowstatus-bot -f

# Restart service
systemctl restart glowstatus-bot
```

### Bot Not Responding to Commands
- Verify bot token is correct
- Check bot has proper permissions in Discord
- Ensure bot is actually in your server

### Permission Errors
- Bot needs Administrator permission OR:
  - Manage Server
  - Manage Roles
  - Manage Channels
  - Send Messages

## Cost Comparison

| Platform | Cost | Setup Time | Reliability |
|----------|------|------------|-------------|
| Railway (Free) | $0/month | 5 minutes | Good |
| DigitalOcean | $5/month | 15 minutes | Excellent |
| Raspberry Pi | $50 once | 30 minutes | Excellent |
| Render (Free) | $0/month | 5 minutes | Fair (sleeps) |

## Security Checklist

- [ ] Never commit bot token to Git
- [ ] Use environment variables for secrets
- [ ] Enable 2FA on hosting account
- [ ] Monitor bot logs regularly
- [ ] Keep dependencies updated

## Need Help?

1. Check the full [Discord README](README.md) for detailed explanations
2. Test locally first: `python discord/setup_discord.py`
3. Verify bot token and permissions
4. Check hosting platform logs for errors

Remember: Discord bots are like web servers - they need to run continuously to work properly!
