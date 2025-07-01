# 🔗 GitHub Webhook Setup Guide

This guide explains how to set up GitHub webhooks for automatic repository updates in your Discord server.

## 📋 Prerequisites

- Discord bot with webhook creation permissions
- Admin access to GitHub repositories
- The Discord server setup bot running

## 🤖 Automatic Setup

The Discord bot will automatically:

1. **Assign Admin Role** to user `severswoed`
2. **Smart Webhook Management**:
   - Detects existing webhooks for the same repository/channel combination
   - Reuses existing webhooks when possible (no new GitHub URLs needed!)
   - Only creates new webhooks when none exist or previous ones are invalid
3. **Generate webhook URLs** and save them to `active_webhooks.json`
4. **Post setup instructions** in the `#dev-updates` channel

### Smart Webhook Benefits

- **No Duplicate Webhooks**: Running setup multiple times won't create unnecessary duplicates
- **Stable URLs**: Existing GitHub webhook configurations remain valid
- **Automatic Verification**: Each setup run checks that existing webhooks still work
- **Manual Override**: Use `!reset_webhooks` if you need to force recreation

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
- `!reset_webhooks` - Delete all webhooks and clear data (admin only)
- `!assign_admin @user` - Manually assign admin role

### Smart Webhook Commands

- **`!webhooks`**: Shows current webhook status and when they were last verified
- **`!remake_webhooks`**: Intelligently recreates webhooks (reuses existing when possible)
- **`!reset_webhooks`**: Forces deletion of all GitHub webhooks and clears data (use if you need a fresh start)

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

## 🔄 Smart Webhook Management

The setup now intelligently handles webhooks:

### First-Time Setup
1. Creates new webhooks for each repository/channel combination
2. Saves webhook URLs to `active_webhooks.json`
3. You configure these URLs in GitHub (one-time setup)

### Subsequent Runs
1. Detects existing webhooks by repository and channel
2. Verifies webhooks are still valid on Discord
3. Reuses existing webhooks (GitHub URLs stay the same!)
4. Only creates new webhooks if previous ones are missing

### When Webhooks Need Recreation
Use `!reset_webhooks` followed by `!remake_webhooks` if:
- Webhooks are corrupted or not working
- You want to change webhook names or configurations
- You're troubleshooting delivery issues

### Troubleshooting Workflow
1. **Check Status**: `!webhooks` - Shows current webhook status
2. **Verify GitHub**: Check webhook delivery in GitHub repo settings
3. **Soft Reset**: `!remake_webhooks` - Recreates with smart reuse
4. **Hard Reset**: `!reset_webhooks` then `!remake_webhooks` - Forces new webhooks

💡 **Pro Tip**: Most of the time you won't need to update GitHub webhook URLs anymore!

---

**Note**: Keep webhook URLs secure and don't share them publicly. They provide direct access to post in your Discord channels.
