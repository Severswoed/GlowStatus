# GlowStatus Discord Setup

Automated setup for the GlowStatus Discord community server, following Discord best practices for community growth and management.

## Before You Start

**Should you create a Discord server for GlowStatus?** 

Our setup follows proven best practices from successful Discord communities:

✅ **Specific Topic**: GlowStatus has a clear, focused purpose - smart LED status lighting integration  
✅ **Community Benefit**: Real-time support, feature discussions, and user showcase opportunities  
✅ **Fills a Gap**: Dedicated space for hardware + software integration discussions  
✅ **Committed Leadership**: Long-term commitment to community growth over personal ownership  

## Quick Setup

1. **Create Discord Bot:**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create new application → Bot
   - Copy bot token
   - **IMPORTANT:** Enable these privileged intents:
     - ✅ Server Members Intent
     - ✅ Message Content Intent

2. **Bot Permissions:**
   When inviting the bot to your server, ensure it has:
   - ✅ **Administrator** (recommended for full automation)
   - OR these individual permissions:
     - Manage Server
     - Manage Roles  
     - Manage Channels
     - Manage Webhooks
     - View Channels
     - Send Messages
     - Embed Links
     - Attach Files

3. **Set Environment Variable:**
   ```bash
   # Windows
   set DISCORD_BOT_TOKEN=your_bot_token_here
   
   # macOS/Linux
   export DISCORD_BOT_TOKEN="your_bot_token_here"
   ```

4. **Install Dependencies:**
   ```bash
   pip install discord.py aiohttp
   ```

5. **Run Setup:**
   ```bash
   python discord/setup_discord.py
   ```

## Manual Setup Steps

If you prefer manual setup, follow these steps in Discord:

### 1. Server Settings
- **Name:** GlowStatus
- **Icon:** Upload your logo with glow effect
- **Banner:** Use gradient banner (Boost Level 2+ required)

### 2. Create Roles
- ✨ Sponsor (Gold color)
- 🧪 Beta Tester (Purple color)  
- ⚙️ Dev Team (Red color)
- 🖥️ Support (Cyan color)
- 🤖 Bots (Gray color)

### 3. Channel Protection
For each protected channel:
1. Right-click channel → Edit Channel
2. Go to Permissions
3. Add 🤖 Bots role
4. Set: ❌ Send Messages, ❌ Embed Links, ❌ Attach Files

### 4. GitHub Integration
1. Go to your GitHub repo → Settings → Webhooks
2. Add webhook: `https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN/github`
3. Select events: Push, Pull Request, Release, Issues
4. Content type: `application/json`

## Channel Structure

```
🟢 Info
├── #welcome
├── #rules  
└── #announcements

🔧 Support
├── #setup-help
├── #feature-requests
└── #integration-requests

🔨 Development  
├── #dev-updates (bot-allowed)
├── #cli-version-v1
├── #app-version-v2
└── #api-dev

☕ Lounge
├── #general
└── #show-your-glow
```

## Channel Structure Reasoning

Our channel organization follows proven Discord best practices:

### 🟢 Info Category
- **#welcome**: First impression with key links and channel guide
- **#rules**: Community guidelines (linked in default invites for new user safety)  
- **#announcements**: Official updates to avoid information fragmentation

### 🔧 Support Category  
- **#setup-help**: Focused troubleshooting and installation questions
- **#feature-requests**: Community-driven development input
- **#integration-requests**: Hardware brand/platform support requests

### 🔨 Development Category
- **#dev-updates**: Automated GitHub activity feed
- **#cli-version-v1**: Legacy version support 
- **#app-version-v2**: Current version discussions
- **#api-dev**: Technical implementation discussions

### ☕ Lounge Category
- **#general**: Off-topic community building
- **#show-your-glow**: User setup showcases and inspiration

**Why This Structure Works:**
1. **Purpose-Driven**: Every channel has a clear, specific function
2. **Growth-Friendly**: Structure scales from 10 to 10,000+ members
3. **Support-Focused**: Multiple dedicated help channels prevent overwhelming 
4. **Community-Building**: Balance of technical and social spaces
5. **Search-Friendly**: Logical organization helps users find relevant discussions

## Bot Protection Rules

### Protected Channels (No bot posting):
- #welcome, #rules, #general, #show-your-glow, #feature-requests

### Bot-Allowed Channels:
- #dev-updates, #announcements

### Webhook-Only Channels:
- Use Discord webhook integration for GitHub updates

## Environment Setup

Create a `.env` file in the root directory:
```env
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_WEBHOOK_URL=your_webhook_url_here
```

## Server Invite

After setup, create an invite link with appropriate permissions:
- Manage Channels
- Manage Roles
- Send Messages
- Embed Links
- Add Reactions
- Use External Emojis

## Moderation Guidelines

1. **Welcome new users** with a friendly greeting
2. **Keep discussions on-topic** in respective channels
3. **Encourage screenshot sharing** in #show-your-glow
4. **Direct support questions** to appropriate channels
5. **No spam or self-promotion** without permission

## Automation Features

- **Auto-role assignment** for GitHub sponsors
- **Welcome message** with embedded links
- **GitHub activity feed** in #dev-updates
- **Release announcements** in #announcements
- **Bot spam protection** on community channels

## Troubleshooting

### Permission Errors (403 Forbidden)

**Error:** `403 Forbidden (error code: 50013): Missing Permissions`
**Solution:**
1. Re-invite bot with Administrator permission
2. Or grant these individual permissions:
   - Manage Server (for server settings)
   - Manage Roles (for role creation/assignment)
   - Manage Channels (for channel creation/editing)
   - Manage Webhooks (for GitHub integration)

**Error:** `403 Forbidden (error code: 50001): Missing Access`
**Solution:**
1. Check bot role hierarchy - bot role must be higher than roles it manages
2. Ensure bot has "View Channels" permission
3. Verify bot is actually in the server

### Intent Warnings

**Warning:** `Privileged message content intent is missing`
**Solution:**
1. Go to Discord Developer Portal
2. Select your application → Bot
3. Enable "Message Content Intent"
4. Save changes and restart bot

### Bot Not Responding
1. Check bot token is correct
2. Verify bot has necessary permissions
3. Ensure bot is invited to the server
4. Check console for error messages

### Auto-Moderation Not Working
**Error:** Auto-mod rules failing to create
**Solution:**
1. Ensure server has Community features enabled
2. Bot needs "Manage Server" permission
3. Check if server already has max auto-mod rules (Discord limits apply)

### Webhook Creation Fails
**Error:** Cannot create webhooks for GitHub integration
**Solution:**
1. Bot needs "Manage Webhooks" permission
2. Check if channel already has max webhooks (10 per channel limit)
3. Verify target channels exist before running setup

### Channels Not Creating
1. Bot needs "Manage Channels" permission
2. Check for existing channels with same names
3. Verify category limits (50 channels per category)

### Permissions Not Working
1. Bot role must be above roles it manages
2. Check channel-specific permission overrides
3. Verify bot has "Manage Roles" permission

## Advanced Moderation Features

### Quarantine System
- New accounts (<24 hours) automatically quarantined
- Limited channel access until manual verification
- Prevents bot raids and spam account creation
- Staff can manually quarantine suspicious users with `!quarantine @user reason`

### Auto-Moderation Rules
- **Spam Protection**: Detects repetitive messages and rapid posting
- **Invite Blocking**: Prevents unauthorized Discord server promotion
- **Link Filtering**: Blocks known malicious and suspicious shortened URLs
- **Caps Control**: Removes messages with excessive uppercase (>70%)

### Staff Commands
- `!quarantine @user [reason]` - Restrict user to quarantine channel
- `!unquarantine @user` - Remove quarantine and grant verified role
- `!verify @user` - Manually verify a user without quarantine
- `!lockdown [#channel]` - Prevent new messages in channel
- `!unlock [#channel]` - Remove lockdown restrictions
- `!webhooks` - List active GitHub webhook configurations
- `!remake_webhooks` - Recreate GitHub webhooks (admin only)

### Security Monitoring
- **Account Age Tracking**: Logs when users join with very new accounts
- **Message Pattern Detection**: Identifies potential spam or bot behavior  
- **Suspicious Link Blocking**: Real-time filtering of dangerous URLs
- **Rate Limiting**: Slow mode on channels prone to spam

### Escalation Process
1. **Auto-Mod**: Bot handles obvious violations automatically
2. **Quarantine**: Staff isolate suspicious users for investigation
3. **Manual Review**: Human judgment for complex situations
4. **Documentation**: All actions logged for accountability
5. **Appeals**: Clear process for users to contest moderation decisions

## Discord Community Best Practices

Our Discord setup incorporates proven strategies from successful communities:

### Channel Organization
- **Clear Purpose**: Each channel has a specific, well-defined purpose
- **Strategic Order**: Important channels (rules, announcements) at the top
- **Limited Categories**: Focused structure prevents overwhelming new users
- **No Redundancy**: Avoid duplicate channels that fragment discussions

### Role Management  
- **Earned Privileges**: Roles provide meaningful benefits, not just decoration
- **Security First**: Bot permissions are minimal and specific to their function
- **No "Owner" Showcase**: Leadership stays integrated with the community
- **Verification Required**: New members must prove legitimacy before full access

### Growth Strategy
- **Quality over Quantity**: Better to have 50 engaged users than 500 lurkers
- **Topic-Focused**: Everything relates back to GlowStatus and smart lighting
- **No Generic Elements**: Avoid becoming just another "general" server
- **External Outreach**: Connect with existing smart home and developer communities

### Moderation Philosophy
- **Automated Security**: Bot handles spam, raids, and obvious rule violations
- **Human Judgment**: Complex situations require staff intervention
- **Quarantine System**: New/suspicious accounts get limited access initially
- **Clear Consequences**: Rules and punishments are transparent

### What We DON'T Do
❌ **Level/XP Systems**: These encourage spam over meaningful conversation  
❌ **Generic Game Bots**: These don't help GlowStatus stand out  
❌ **Random Invite Rewards**: This violates Discord ToS and brings low-quality members  
❌ **Staff Showcase**: Leadership isn't about status but about serving the community  
❌ **Multiple General Channels**: This fragments discussions unnecessarily  

### Community Engagement
- **Regular Updates**: Consistent development progress shared with the community
- **User Showcases**: Dedicated space for users to share their GlowStatus setups
- **Feature Feedback**: Community input directly influences development priorities
- **Technical Support**: Real-time help for setup and troubleshooting issues

### Security Measures
- **Auto-Moderation**: Blocks spam, suspicious links, and invite farming
- **Account Age Screening**: New accounts get extra scrutiny  
- **Permission Layering**: Multiple security levels prevent single points of failure
- **Staff Coverage**: Moderation available across different timezones

### Growth Milestones
Our community goals based on proven scaling patterns:
- **0-50 members**: Focus on core contributors and early adopters
- **50-200 members**: Establish regular content and support patterns  
- **200-500 members**: Add specialized channels and expand moderation
- **500+ members**: Consider advanced features and community events

## Community Building & Advertising

### How to Grow the GlowStatus Discord

**Smart Outreach:**
- Share in relevant subreddits: r/smarthome, r/homeautomation, r/battlestations
- Post in developer communities: r/Python, r/opensource, GitHub Discussions
- Connect with hardware communities: r/govee, r/philipshue, smart lighting forums
- Engage in calendar/productivity communities where GlowStatus adds value

**Quality over Quantity:**
- Only invite people genuinely interested in smart lighting or productivity tools
- Share when providing helpful answers, not as random promotion
- Let satisfied users become natural advocates through word-of-mouth

**Content Strategy:**
- Regular development updates and behind-the-scenes content
- User spotlight features showcasing creative GlowStatus setups
- Technical tutorials and integration guides
- Feature announcement and roadmap discussions

### Server Listing Sites

For increased discoverability, consider listing on:
- **invite.gg** - Custom invite links and server discovery
- **discordservers.com** - Popular server directory with search functionality
- **carbonitex.net** - Server statistics and listing platform

### What NOT to Do

❌ **Random Discord Spam**: Never post invite links in unrelated servers  
❌ **Reward Invites**: Incentivizing invites brings uninterested users  
❌ **Generic Promotion**: "Join my server" posts without context  
❌ **Off-Topic Shares**: Only share where GlowStatus genuinely adds value  

### Building Engagement

**Regular Activities:**
- Weekly development updates with screenshots/demos
- Monthly "Setup Showcase" where users share their lighting configurations
- Feature request voting and community roadmap discussions
- Beta testing opportunities for active community members

**Community Events:**
- GlowStatus setup competitions with sponsor prizes
- Developer Q&A sessions about the project's future
- Integration challenges: "Light up your ___ with GlowStatus"
- Troubleshooting sessions for complex hardware setups

### External Partnerships

**Strategic Connections:**
- Smart home influencers and content creators
- Home office setup communities
- Developer tool communities
- Hardware review channels and blogs

Remember: The goal is building a sustainable community of engaged users, not accumulating member count numbers.

## Next Steps

1. **Set up GitHub webhooks** for automated updates
2. **Create custom emojis** for GlowStatus branding
3. **Add server boosters perks** for enhanced features
4. **Set up automated moderation** with bots like MEE6
5. **Create community events** and announcements
