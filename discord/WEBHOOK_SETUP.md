# 🔗 GitHub Webhook Setup Guide

This guide explains how to set up GitHub webhooks for automatic repository updates in your Discord server.

## 📋 Prerequisites

- Discord bot with webhook creation permissions
- Admin access to GitHub repositories
- The Discord server setup bot running

## 🤖 Automatic Setup

The Discord bot will automatically:

1. **Assign Admin Role** to user `severswoed`
2. **Create Webhooks** for both repositories:
   - `Severswoed/GlowStatus` → `#dev-updates`
   - `Severswoed/GlowStatus-site` → `#dev-updates`
3. **Generate webhook URLs** and save them to `active_webhooks.json`
4. **Post setup instructions** in the `#dev-updates` channel

## 🛠️ Manual GitHub Configuration

After running the bot, you'll need to configure each repository:

### For GlowStatus Repository

1. Go to https://github.com/Severswoed/GlowStatus
2. Click **Settings** → **Webhooks** → **Add webhook**
3. **Payload URL**: Use the webhook URL from `#dev-updates` channel or `active_webhooks.json`
4. **Content type**: `application/json`
5. **Events**: Select individual events:
   - ✅ Pushes
   - ✅ Pull requests
   - ✅ Releases
   - ✅ Issues
6. **Active**: ✅ Checked
7. Click **Add webhook**

### For GlowStatus-site Repository

1. Go to https://github.com/Severswoed/GlowStatus-site
2. Click **Settings** → **Webhooks** → **Add webhook**
3. **Payload URL**: Use the webhook URL from `#dev-updates` channel or `active_webhooks.json`
4. **Content type**: `application/json`
5. **Events**: Select individual events:
   - ✅ Pushes
   - ✅ Pull requests
   - ✅ Releases
6. **Active**: ✅ Checked
7. Click **Add webhook**

## 📱 Bot Commands

Use these commands to manage webhooks:

- `!webhooks` - List all active GitHub webhooks
- `!remake_webhooks` - Recreate all webhooks (admin only)
- `!assign_admin @user` - Manually assign admin role

## 🔒 Security Features

- **Webhook URLs are hidden** in spoiler tags to prevent abuse
- **Admin permissions required** for webhook management
- **Automatic owner detection** assigns admin role to `severswoed`
- **Channel-specific posting** keeps updates organized

## 📄 Generated Files

The bot creates these files:

- `active_webhooks.json` - Contains all webhook URLs and configuration
- Webhook URLs are saved securely and can be regenerated if needed

## 🚨 Troubleshooting

### Bot can't create webhooks
- Ensure bot has **Manage Webhooks** permission
- Check that target channels exist
- Verify bot is in the server

### GitHub webhook delivery fails
- Check webhook URL is correct
- Verify Content-Type is `application/json`
- Test webhook in GitHub settings

### Missing admin privileges
- Run `!assign_admin @severswoed` manually
- Check bot has permission to assign roles
- Verify admin role exists

## 📊 Webhook Events

### GlowStatus Repository
- **Push events** - Code commits and merges
- **Pull requests** - New PRs, reviews, merges
- **Releases** - Version releases and tags
- **Issues** - Bug reports and feature requests

### GlowStatus-site Repository  
- **Push events** - Website updates
- **Pull requests** - Site improvements
- **Releases** - Site version releases

## 🔄 Regenerating Webhooks

If webhooks stop working:

1. Use `!remake_webhooks` command in Discord
2. Update GitHub repository settings with new URLs
3. Test webhook delivery in GitHub settings

---

**Note**: Keep webhook URLs secure and don't share them publicly. They provide direct access to post in your Discord channels.
