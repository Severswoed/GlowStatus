"""
Automated Discord Server Setup for GlowStatus
Creates channels, roles, and permissions for the GlowStatus community
"""

import discord
from discord.ext import commands
import asyncio
import json
import os
import aiohttp
from datetime import datetime

# Configuration
CONFIG = {
    "server_name": "GlowStatus",
    "bot_token": os.getenv("DISCORD_BOT_TOKEN"),  # Set this in your environment
    "channels": {
        "info": [
            {"name": "welcome", "description": "🌟 Welcome to GlowStatus! React with 👋 to get verified and access all channels. Your journey to smart lighting starts here!"},
            {"name": "rules", "description": "📋 Community guidelines and code of conduct. Be awesome, be respectful, and help us build an amazing community together."},
            {"name": "announcements", "description": "📢 Official updates, new releases, feature announcements, and roadmap reveals. Stay in the loop with GlowStatus development!"}
        ],
        "support": [
            {"name": "setup-help", "description": "🔧 Stuck with installation, configuration, or API setup? Get help from the community and maintainers. No question is too basic!"},
            {"name": "feature-requests", "description": "💡 Got ideas to make GlowStatus even better? Share your feature requests, vote on others, and shape the future of the project!"},
            {"name": "integration-requests", "description": "🔗 Want support for your favorite smart light brand? Request integrations for Philips Hue, LIFX, Nanoleaf, and more!"}
        ],
        "development": [
            {"name": "dev-updates", "description": "🤖 Automated GitHub notifications for commits, PRs, releases, and issues. Watch GlowStatus development in real-time!"},
            {"name": "cli-version-v1", "description": "💻 Discussion and support for the original CLI version of GlowStatus. Legacy users welcome!"},
            {"name": "app-version-v2", "description": "🖥️ GUI installer, settings interface, and v2 app discussions. The future of GlowStatus user experience!"},
            {"name": "api-dev", "description": "⚙️ API development, integrations, webhooks, and technical architecture discussions. For developers and power users."}
        ],
        "lounge": [
            {"name": "general", "description": "☕ Casual conversations, introductions, and off-topic discussions. Get to know the GlowStatus community!"},
            {"name": "show-your-glow", "description": "📸 Show off your GlowStatus setup! Share photos, videos, and creative uses of your smart lighting system. Inspiration central!"}
        ]
    },
    "roles": {
        "admin": {"name": "🛡️ Admin", "color": 0xFF0000, "permissions": ["administrator"]},
        "moderator": {"name": "🔨 Moderator", "color": 0xFF6600, "permissions": ["manage_messages", "manage_channels", "kick_members", "ban_members"]},
        "sponsor": {"name": "✨ Sponsor", "color": 0xFFD700, "permissions": ["embed_links", "attach_files"]},
        "beta_tester": {"name": "🧪 Beta Tester", "color": 0x9932CC, "permissions": ["embed_links"]},
        "dev_team": {"name": "⚙️ Dev Team", "color": 0xFF4500, "permissions": ["manage_messages", "embed_links", "attach_files"]},
        "support": {"name": "🖥️ Support", "color": 0x00CED1, "permissions": ["manage_messages"]},
        "verified": {"name": "✅ Verified", "color": 0x00FF00, "permissions": []},
        "trusted_bots": {"name": "🤖 Trusted Bots", "color": 0x808080, "permissions": ["embed_links", "attach_files"]},
        "quarantine": {"name": "⚠️ Quarantine", "color": 0x800000, "permissions": []}
    },
    "protected_channels": ["welcome", "rules", "general", "show-your-glow", "feature-requests"],
    "bot_allowed_channels": ["dev-updates", "announcements"],
    "security": {
        "verification_level": "medium",  # none, low, medium, high, very_high
        "content_filter": "all_members",  # disabled, members_without_roles, all_members
        "require_verified_email": True,
        "rate_limit_per_user": 5,  # seconds between messages for new users
        "auto_moderation": {
            "enabled": True,
            "block_spam": True,
            "block_invites": True,
            "block_excessive_caps": True,
            "block_suspicious_links": True
        }
    },
    "owner": {
        "username": "severswoed",  # Discord username (without @)
        "user_id": None,  # Will be set automatically when found
        "auto_assign_admin": True
    },
    "additional_admins": [
        {
            "username": "unkai.gaming_62749",  # Discord username (without @)
            "user_id": None,  # Will be set automatically when found
            "auto_assign_admin": True
        }
    ],
    "github_webhooks": {
        "enabled": True,
        "repositories": [
            {
                "name": "GlowStatus",
                "owner": "Severswoed",
                "channel": "dev-updates",
                "events": ["push", "pull_request", "release", "issues"]
            },
            {
                "name": "GlowStatus-site", 
                "owner": "Severswoed",
                "channel": "dev-updates",
                "events": ["push", "pull_request", "release"]
            }
        ]
    }
}

class GlowStatusSetup(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True  # For member join/leave events
        intents.message_content = True  # For content filtering
        intents.moderation = True  # For auto-mod features
        intents.reactions = True  # For reaction events
        super().__init__(command_prefix='!', intents=intents)

    async def on_ready(self):
        print(f'Bot logged in as {self.user}')
        guild = discord.utils.get(self.guilds, name=CONFIG["server_name"])
        if guild:
            await self.setup_server(guild)
            await self.assign_owner_privileges(guild)
        else:
            print(f"Server '{CONFIG['server_name']}' not found!")

    async def on_member_join(self, member):
        """Handle new member security screening"""
        await self.screen_new_member(member)

    async def on_message(self, message):
        """Monitor messages for security threats"""
        if message.author.bot:
            return
        
        await self.check_message_security(message)
        await self.process_commands(message)

    async def setup_server(self, guild):
        """Setup the entire server structure"""
        print(f"Setting up server: {guild.name}")
        
        # Apply server security settings first
        await self.setup_server_security(guild)
        
        # Create roles first
        await self.create_roles(guild)
        
        # Create categories and channels
        await self.create_channels(guild)
        
        # Set up permissions
        await self.setup_permissions(guild)
        
        # Setup auto-moderation
        await self.setup_auto_moderation(guild)
        
        # Create welcome message
        await self.setup_welcome_channel(guild)
        
        # Setup GitHub webhooks
        await self.setup_github_webhooks(guild)
        
        # Send server invite to additional admins
        await self.send_admin_invites(guild)
        
        print("Server setup complete!")

    async def create_roles(self, guild):
        """Create all necessary roles"""
        print("Creating roles...")
        existing_roles = [role.name for role in guild.roles]
        
        for role_key, role_config in CONFIG["roles"].items():
            if role_config["name"] not in existing_roles:
                await guild.create_role(
                    name=role_config["name"],
                    color=discord.Color(role_config["color"]),
                    reason="GlowStatus server setup"
                )
                print(f"Created role: {role_config['name']}")

    async def create_channels(self, guild):
        """Create all channels with categories"""
        print("Creating channels...")
        
        for category_name, channels in CONFIG["channels"].items():
            # Create category
            category_emoji = {
                "info": "🟢",
                "support": "🔧", 
                "development": "🔨",
                "lounge": "☕"
            }
            
            category_display_name = f"{category_emoji.get(category_name, '')} {category_name.title()}"
            category = discord.utils.get(guild.categories, name=category_display_name)
            
            if not category:
                category = await guild.create_category(category_display_name)
                print(f"Created category: {category_display_name}")
            
            # Create channels in category
            for channel_config in channels:
                channel_name = channel_config["name"]
                existing_channel = discord.utils.get(guild.channels, name=channel_name)
                
                if not existing_channel:
                    await guild.create_text_channel(
                        channel_name,
                        category=category,
                        topic=channel_config["description"]
                    )
                    print(f"Created channel: #{channel_name}")

    async def setup_permissions(self, guild):
        """Setup channel permissions to protect from bot spam and enhance security"""
        print("Setting up permissions...")
        
        # Get security roles
        trusted_bots_role = discord.utils.get(guild.roles, name=CONFIG["roles"]["trusted_bots"]["name"])
        quarantine_role = discord.utils.get(guild.roles, name=CONFIG["roles"]["quarantine"]["name"])
        verified_role = discord.utils.get(guild.roles, name=CONFIG["roles"]["verified"]["name"])
        
        # Set @everyone permissions (restrict by default)
        everyone_role = guild.default_role
        
        # Restrict bots from protected channels
        for channel_name in CONFIG["protected_channels"]:
            channel = discord.utils.get(guild.channels, name=channel_name)
            if channel:
                # Block untrusted bots
                if trusted_bots_role:
                    await channel.set_permissions(
                        trusted_bots_role,
                        send_messages=False,
                        embed_links=False,
                        attach_files=False,
                        reason="Protect from bot spam"
                    )
                
                # Quarantined users can only read
                if quarantine_role:
                    await channel.set_permissions(
                        quarantine_role,
                        send_messages=False,
                        add_reactions=False,
                        attach_files=False,
                        embed_links=False,
                        reason="Quarantine restrictions"
                    )
                
                # Apply rate limiting for new users
                await channel.edit(
                    slowmode_delay=CONFIG["security"]["rate_limit_per_user"],
                    reason="Rate limiting for security"
                )
                
                print(f"🔒 Secured #{channel_name}")

        # Allow trusted bots in specific channels
        for channel_name in CONFIG["bot_allowed_channels"]:
            channel = discord.utils.get(guild.channels, name=channel_name)
            if channel and trusted_bots_role:
                await channel.set_permissions(
                    trusted_bots_role,
                    send_messages=True,
                    embed_links=True,
                    attach_files=True,
                    reason="Allow trusted bot posting"
                )
                print(f"✅ Allowed trusted bots in #{channel_name}")

        # Create a quarantine channel if needed
        quarantine_channel = discord.utils.get(guild.channels, name="quarantine")
        if not quarantine_channel and quarantine_role:
            quarantine_category = discord.utils.get(guild.categories, name="🔒 Moderation")
            if not quarantine_category:
                quarantine_category = await guild.create_category("🔒 Moderation")
            
            quarantine_channel = await guild.create_text_channel(
                "quarantine",
                category=quarantine_category,
                topic="Temporary holding area for new/suspicious accounts"
            )
            
            # Only quarantined users and staff can see this channel
            await quarantine_channel.set_permissions(everyone_role, view_channel=False)
            await quarantine_channel.set_permissions(quarantine_role, view_channel=True, send_messages=True)
            
            print("🔒 Created quarantine channel")

    async def setup_welcome_channel(self, guild):
        """Create welcome message with links"""
        welcome_channel = discord.utils.get(guild.channels, name="welcome")
        if not welcome_channel:
            print("Welcome channel not found!")
            return

        welcome_embed = discord.Embed(
            title="🌟 Welcome to GlowStatus!",
            description="Light up your availability with smart LED integration",
            color=0x00FF7F
        )
        
        welcome_embed.add_field(
            name="🔗 Important Links",
            value=(
                "🌐 **Website:** [glowstatus.app](https://glowstatus.app)\n"
                "💻 **GitHub:** [Severswoed/GlowStatus](https://github.com/Severswoed/GlowStatus)\n"
                "💡 **Sponsor:** [GitHub Sponsors](https://github.com/sponsors/Severswoed)\n"
                "📬 **Contact:** glowstatus.app@gmail.com"
            ),
            inline=False
        )
        
        welcome_embed.add_field(
            name="📁 Channel Guide",
            value=(
                "🟢 **Info:** Welcome, rules, announcements\n"
                "🔧 **Support:** Get help and request features\n"
                "🔨 **Development:** Updates and technical discussion\n"
                "☕ **Lounge:** General chat and show off your setup!"
            ),
            inline=False
        )
        
        welcome_embed.set_footer(text="React with 👋 to get started!")
        
        # Clear existing messages and post welcome
        await welcome_channel.purge()
        message = await welcome_channel.send(embed=welcome_embed)
        await message.add_reaction("👋")

    async def setup_server_security(self, guild):
        """Apply server-wide security settings"""
        print("Configuring server security...")
        
        # Set verification level
        verification_levels = {
            "none": discord.VerificationLevel.none,
            "low": discord.VerificationLevel.low,
            "medium": discord.VerificationLevel.medium,
            "high": discord.VerificationLevel.high,
            "very_high": discord.VerificationLevel.highest
        }
        
        # Set content filter
        content_filters = {
            "disabled": discord.ContentFilter.disabled,
            "members_without_roles": discord.ContentFilter.no_role,
            "all_members": discord.ContentFilter.all_members
        }
        
        try:
            await guild.edit(
                verification_level=verification_levels[CONFIG["security"]["verification_level"]],
                explicit_content_filter=content_filters[CONFIG["security"]["content_filter"]],
                reason="GlowStatus security setup"
            )
            print(f"Applied security settings: {CONFIG['security']['verification_level']} verification")
        except Exception as e:
            print(f"Error setting server security: {e}")

    async def setup_auto_moderation(self, guild):
        """Setup auto-moderation rules"""
        if not CONFIG["security"]["auto_moderation"]["enabled"]:
            return
            
        print("Setting up auto-moderation...")
        
        try:
            # Create spam protection rule
            if CONFIG["security"]["auto_moderation"]["block_spam"]:
                await guild.create_auto_moderation_rule(
                    name="Anti-Spam Protection",
                    event_type=discord.AutoModRuleEventType.message_send,
                    trigger=discord.AutoModTrigger(
                        type=discord.AutoModTriggerType.spam
                    ),
                    actions=[
                        discord.AutoModRuleAction(
                            type=discord.AutoModRuleActionType.block_message
                        ),
                        discord.AutoModRuleAction(
                            type=discord.AutoModRuleActionType.timeout,
                            metadata=discord.AutoModActionMetadata(duration_seconds=300)
                        )
                    ],
                    enabled=True,
                    reason="GlowStatus anti-spam protection"
                )
                print("Created anti-spam rule")

            # Create invite link blocking rule  
            if CONFIG["security"]["auto_moderation"]["block_invites"]:
                await guild.create_auto_moderation_rule(
                    name="Block Invite Links",
                    event_type=discord.AutoModRuleEventType.message_send,
                    trigger=discord.AutoModTrigger(
                        type=discord.AutoModTriggerType.keyword,
                        keyword_filter=["discord.gg/", "discord.com/invite/", "discordapp.com/invite/"]
                    ),
                    actions=[
                        discord.AutoModRuleAction(
                            type=discord.AutoModRuleActionType.block_message
                        )
                    ],
                    enabled=True,
                    reason="Block unauthorized invite links"
                )
                print("Created invite blocking rule")

        except Exception as e:
            print(f"Auto-moderation setup error: {e}")

    async def screen_new_member(self, member):
        """Screen new members for security threats"""
        guild = member.guild
        
        # Check account age (flag accounts less than 7 days old)
        account_age = (discord.utils.utcnow() - member.created_at).days
        if account_age < 7:
            print(f"⚠️ New account detected: {member.name} (created {account_age} days ago)")
            
            # Apply quarantine role for very new accounts
            if account_age < 1:
                quarantine_role = discord.utils.get(guild.roles, name=CONFIG["roles"]["quarantine"]["name"])
                if quarantine_role:
                    await member.add_roles(quarantine_role, reason="Very new account - quarantine")
                    print(f"🔒 Quarantined {member.name} - account less than 1 day old")

        # Log member join
        print(f"👤 New member: {member.name}#{member.discriminator} (Account: {account_age} days old)")

    async def check_message_security(self, message):
        """Check messages for security threats"""
        if not message.guild:
            return
            
        # Check for excessive caps (more than 70% uppercase)
        if len(message.content) > 10:
            caps_ratio = sum(1 for c in message.content if c.isupper()) / len(message.content)
            if caps_ratio > 0.7 and CONFIG["security"]["auto_moderation"]["block_excessive_caps"]:
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention}, please don't use excessive caps.",
                    delete_after=10
                )
                return

        # Check for suspicious links
        suspicious_domains = [
            "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", 
            "short.link", "cutt.ly", "tiny.cc"
        ]
        
        if any(domain in message.content.lower() for domain in suspicious_domains):
            if CONFIG["security"]["auto_moderation"]["block_suspicious_links"]:
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention}, suspicious links are not allowed. Please use direct links.",
                    delete_after=15
                )
                print(f"🔗 Blocked suspicious link from {message.author.name}")

    @commands.command(name='quarantine')
    @commands.has_permissions(manage_roles=True)
    async def quarantine_user(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Quarantine a suspicious user"""
        quarantine_role = discord.utils.get(ctx.guild.roles, name=CONFIG["roles"]["quarantine"]["name"])
        if not quarantine_role:
            await ctx.send("❌ Quarantine role not found!")
            return
        
        await member.add_roles(quarantine_role, reason=f"Quarantined by {ctx.author}: {reason}")
        await ctx.send(f"🔒 {member.mention} has been quarantined. Reason: {reason}")
        print(f"🔒 {member.name} quarantined by {ctx.author.name}: {reason}")

    @commands.command(name='unquarantine')
    @commands.has_permissions(manage_roles=True)
    async def unquarantine_user(self, ctx, member: discord.Member):
        """Remove quarantine from a user"""
        quarantine_role = discord.utils.get(ctx.guild.roles, name=CONFIG["roles"]["quarantine"]["name"])
        verified_role = discord.utils.get(ctx.guild.roles, name=CONFIG["roles"]["verified"]["name"])
        
        if quarantine_role in member.roles:
            await member.remove_roles(quarantine_role, reason=f"Unquarantined by {ctx.author}")
            if verified_role:
                await member.add_roles(verified_role, reason="Verified after quarantine")
            await ctx.send(f"✅ {member.mention} has been released from quarantine and verified.")
            print(f"✅ {member.name} unquarantined by {ctx.author.name}")
        else:
            await ctx.send(f"❌ {member.mention} is not quarantined.")

    @commands.command(name='verify')
    @commands.has_permissions(manage_roles=True)
    async def verify_user(self, ctx, member: discord.Member):
        """Manually verify a user"""
        verified_role = discord.utils.get(ctx.guild.roles, name=CONFIG["roles"]["verified"]["name"])
        if not verified_role:
            await ctx.send("❌ Verified role not found!")
            return
        
        await member.add_roles(verified_role, reason=f"Manually verified by {ctx.author}")
        await ctx.send(f"✅ {member.mention} has been manually verified.")
        print(f"✅ {member.name} manually verified by {ctx.author.name}")

    @commands.command(name='lockdown')
    @commands.has_permissions(manage_channels=True)
    async def lockdown_channel(self, ctx, channel: discord.TextChannel = None):
        """Lock down a channel to prevent new messages"""
        if not channel:
            channel = ctx.channel
        
        await channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send(f"🔒 {channel.mention} has been locked down.")
        print(f"🔒 Channel {channel.name} locked down by {ctx.author.name}")

    @commands.command(name='unlock')
    @commands.has_permissions(manage_channels=True)
    async def unlock_channel(self, ctx, channel: discord.TextChannel = None):
        """Unlock a channel"""
        if not channel:
            channel = ctx.channel
        
        await channel.set_permissions(ctx.guild.default_role, send_messages=None)
        await ctx.send(f"🔓 {channel.mention} has been unlocked.")
        print(f"🔓 Channel {channel.name} unlocked by {ctx.author.name}")

    @commands.command(name='security_status')
    @commands.has_permissions(manage_guild=True)
    async def security_status(self, ctx):
        """Show current security status of the server"""
        guild = ctx.guild
        
        embed = discord.Embed(
            title="🛡️ Server Security Status",
            color=0x00FF00
        )
        
        embed.add_field(
            name="Verification Level",
            value=str(guild.verification_level).title(),
            inline=True
        )
        
        embed.add_field(
            name="Content Filter",
            value=str(guild.explicit_content_filter).replace('_', ' ').title(),
            inline=True
        )
        
        embed.add_field(
            name="Member Count",
            value=f"{guild.member_count} members",
            inline=True
        )
        
        # Count quarantined users
        quarantine_role = discord.utils.get(guild.roles, name=CONFIG["roles"]["quarantine"]["name"])
        quarantined_count = len(quarantine_role.members) if quarantine_role else 0
        
        embed.add_field(
            name="Quarantined Users",
            value=f"{quarantined_count} users",
            inline=True
        )
        
        await ctx.send(embed=embed)

    async def assign_owner_privileges(self, guild):
        """Assign admin privileges to the server owner and additional admins"""
        if not CONFIG["owner"]["auto_assign_admin"]:
            return
            
        print("Assigning owner and admin privileges...")
        
        # Get admin role
        admin_role = discord.utils.get(guild.roles, name=CONFIG["roles"]["admin"]["name"])
        if not admin_role:
            print("❌ Admin role not found!")
            return
        
        # Find and assign admin to the owner
        owner_member = None
        for member in guild.members:
            if member.name.lower() == CONFIG["owner"]["username"].lower():
                owner_member = member
                CONFIG["owner"]["user_id"] = member.id
                break
        
        if owner_member:
            if admin_role not in owner_member.roles:
                await owner_member.add_roles(admin_role, reason="Server owner - auto-assigned admin")
                print(f"👑 Assigned admin privileges to {owner_member.name} (owner)")
            else:
                print(f"✅ {owner_member.name} (owner) already has admin privileges")
        else:
            print(f"⚠️ Owner '{CONFIG['owner']['username']}' not found in server!")
        
        # Find and assign admin to additional admins
        for admin_config in CONFIG.get("additional_admins", []):
            if not admin_config.get("auto_assign_admin", True):
                continue
                
            admin_member = None
            for member in guild.members:
                if member.name.lower() == admin_config["username"].lower():
                    admin_member = member
                    admin_config["user_id"] = member.id
                    break
            
            if admin_member:
                if admin_role not in admin_member.roles:
                    await admin_member.add_roles(admin_role, reason="Additional admin - auto-assigned")
                    print(f"👑 Assigned admin privileges to {admin_member.name} (additional admin)")
                else:
                    print(f"✅ {admin_member.name} (additional admin) already has admin privileges")
            else:
                print(f"⚠️ Additional admin '{admin_config['username']}' not found in server!")

    async def setup_github_webhooks(self, guild):
        """Setup GitHub webhook integration"""
        if not CONFIG["github_webhooks"]["enabled"]:
            return
            
        print("Setting up GitHub webhooks...")
        
        # Load existing webhook data if it exists
        webhook_file_path = os.path.join(os.path.dirname(__file__), "active_webhooks.json")
        existing_webhooks = {}
        
        try:
            if os.path.exists(webhook_file_path):
                with open(webhook_file_path, 'r') as f:
                    existing_data = json.load(f)
                    for webhook in existing_data.get("webhooks", []):
                        key = (webhook["repository"], webhook["channel"])
                        existing_webhooks[key] = webhook
                print(f"📄 Loaded {len(existing_webhooks)} existing webhooks")
        except Exception as e:
            print(f"⚠️ Could not load existing webhooks: {e}")
        
        # Create webhook information file
        webhook_data = {
            "webhooks": [],
            "setup_instructions": {
                "step_1": "Go to your GitHub repository settings",
                "step_2": "Navigate to 'Webhooks' section", 
                "step_3": "Click 'Add webhook'",
                "step_4": "Use the webhook URLs provided below",
                "step_5": "Set Content type to 'application/json'",
                "step_6": "Select events or choose 'Just the push event' for basic setup"
            }
        }
        
        for repo_config in CONFIG["github_webhooks"]["repositories"]:
            channel = discord.utils.get(guild.channels, name=repo_config["channel"])
            if not channel:
                print(f"❌ Channel #{repo_config['channel']} not found for {repo_config['name']} webhook")
                continue
            
            repo_full_name = f"{repo_config['owner']}/{repo_config['name']}"
            webhook_key = (repo_full_name, repo_config["channel"])
            
            # Check if webhook already exists for this repo/channel combination
            if webhook_key in existing_webhooks:
                existing_webhook = existing_webhooks[webhook_key]
                
                # Verify the webhook still exists on Discord
                try:
                    # Try to fetch webhooks for the channel
                    channel_webhooks = await channel.webhooks()
                    webhook_exists = False
                    
                    for webhook in channel_webhooks:
                        if webhook.name == f"GitHub-{repo_config['name']}":
                            # Update with current webhook info
                            webhook_info = {
                                "repository": repo_full_name,
                                "channel": repo_config["channel"],
                                "webhook_url": webhook.url,
                                "events": repo_config["events"],
                                "setup_date": existing_webhook.get("setup_date", datetime.now().isoformat()),
                                "last_verified": datetime.now().isoformat()
                            }
                            webhook_data["webhooks"].append(webhook_info)
                            webhook_exists = True
                            print(f"♻️ Reusing existing webhook for {repo_full_name} -> #{repo_config['channel']}")
                            break
                    
                    if webhook_exists:
                        continue
                    else:
                        print(f"🔄 Existing webhook for {repo_full_name} not found in channel, creating new one...")
                        
                except Exception as e:
                    print(f"⚠️ Could not verify existing webhook for {repo_full_name}: {e}")
                    print(f"🔄 Creating new webhook...")
            
            # Create new webhook for the channel
            try:
                webhook = await channel.create_webhook(
                    name=f"GitHub-{repo_config['name']}",
                    reason=f"GitHub webhook for {repo_config['owner']}/{repo_config['name']}"
                )
                
                webhook_info = {
                    "repository": repo_full_name,
                    "channel": repo_config["channel"],
                    "webhook_url": webhook.url,
                    "events": repo_config["events"],
                    "setup_date": datetime.now().isoformat()
                }
                
                webhook_data["webhooks"].append(webhook_info)
                print(f"✅ Created new webhook for {repo_full_name} -> #{repo_config['channel']}")
                
            except Exception as e:
                print(f"❌ Error creating webhook for {repo_config['name']}: {e}")
        
        # Save webhook information to file
        try:
            with open(webhook_file_path, 'w') as f:
                json.dump(webhook_data, f, indent=2)
            print(f"📄 Webhook information saved to: {webhook_file_path}")
        except Exception as e:
            print(f"❌ Error saving webhook data: {e}")
        
        # Send setup instructions to dev-updates channel
        await self.send_webhook_instructions(guild, webhook_data)

    async def send_webhook_instructions(self, guild, webhook_data):
        """Send GitHub webhook setup instructions privately to severswoed"""
        if not webhook_data["webhooks"]:
            return
        
        # Find severswoed user
        owner_member = None
        for member in guild.members:
            if member.name.lower() == CONFIG["owner"]["username"].lower():
                owner_member = member
                break
        
        if not owner_member:
            print(f"⚠️ Could not find {CONFIG['owner']['username']} to send private webhook info")
            return
        
        # Send webhook URLs privately via DM
        try:
            embed = discord.Embed(
                title="🔗 GitHub Webhook Setup (PRIVATE)",
                description="🔒 **CONFIDENTIAL** - Your webhook URLs for GitHub integration",
                color=0x238636
            )
            
            for webhook in webhook_data["webhooks"]:
                embed.add_field(
                    name=f"📦 {webhook['repository']}",
                    value=(
                        f"**Channel:** #{webhook['channel']}\n"
                        f"**Events:** {', '.join(webhook['events'])}\n"
                        f"**Webhook URL:** {webhook['webhook_url']}\n"
                        f"⚠️ Keep this URL secret!"
                    ),
                    inline=False
                )
            
            embed.add_field(
                name="🛠️ Setup Steps",
                value=(
                    "1. Go to your GitHub repository\n"
                    "2. Settings → Webhooks → Add webhook\n"
                    "3. Paste the webhook URL above\n"
                    "4. Content type: `application/json`\n"
                    "5. Select events or use 'Just the push event'\n"
                    "6. Click 'Add webhook'\n\n"
                    "💡 **Smart Setup:** Existing webhooks are reused automatically!\n"
                    "Only new webhook URLs need to be added to GitHub."
                ),
                inline=False
            )
            
            embed.set_footer(text="This message was sent privately for security. Do not share webhook URLs.")
            
            await owner_member.send(embed=embed)
            print(f"📧 Sent private webhook setup instructions to {owner_member.name}")
            
        except discord.Forbidden:
            print(f"❌ Could not send DM to {owner_member.name} - they may have DMs disabled")
            print("⚠️ Webhook URLs are saved in active_webhooks.json file instead")
        except Exception as e:
            print(f"❌ Error sending private webhook info: {e}")
        
        # Send public notification (without URLs) to dev-updates channel
        dev_channel = discord.utils.get(guild.channels, name="dev-updates")
        if dev_channel:
            public_embed = discord.Embed(
                title="✅ GitHub Webhooks Configured",
                description="GitHub integration has been set up successfully!",
                color=0x00FF00
            )
            
            public_embed.add_field(
                name="📦 Repositories Connected",
                value="\n".join([f"• {webhook['repository']}" for webhook in webhook_data["webhooks"]]),
                inline=False
            )
            
            public_embed.add_field(
                name="🔔 What to Expect",
                value=(
                    "This channel will now receive automatic updates for:\n"
                    "• New commits and pushes\n"
                    "• Pull requests\n"
                    "• New releases\n"
                    "• Issues (for main repo)"
                ),
                inline=False
            )
            
            public_embed.set_footer(text="Webhook configuration sent privately to server owner")
            
            await dev_channel.send(embed=public_embed)
            print("📋 Sent public webhook notification to #dev-updates")

    @commands.command(name='webhooks')
    @commands.has_permissions(manage_guild=True)
    async def list_webhooks(self, ctx):
        """List all active GitHub webhooks"""
        try:
            webhook_file_path = os.path.join(os.path.dirname(__file__), "active_webhooks.json")
            if not os.path.exists(webhook_file_path):
                await ctx.send("❌ No webhook configuration found. Run setup first.")
                return
            
            with open(webhook_file_path, 'r') as f:
                webhook_data = json.load(f)
            
            if not webhook_data["webhooks"]:
                await ctx.send("❌ No active webhooks found.")
                return
            
            embed = discord.Embed(
                title="🔗 Active GitHub Webhooks",
                color=0x238636
            )
            
            for webhook in webhook_data["webhooks"]:
                embed.add_field(
                    name=f"📦 {webhook['repository']}",
                    value=(
                        f"**Channel:** #{webhook['channel']}\n"
                        f"**Events:** {', '.join(webhook['events'])}\n"
                        f"**Setup:** {webhook['setup_date'][:10]}"
                    ),
                    inline=True
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error retrieving webhook data: {e}")

    @commands.command(name='remake_webhooks')
    @commands.has_permissions(administrator=True)
    async def remake_webhooks(self, ctx):
        """Recreate all GitHub webhooks (admin only)"""
        await ctx.send("🔄 Recreating GitHub webhooks...")
        await self.setup_github_webhooks(ctx.guild)
        await ctx.send("✅ GitHub webhooks have been recreated!")

    @commands.command(name='assign_admin')
    @commands.has_permissions(administrator=True)
    async def assign_admin_command(self, ctx, member: discord.Member):
        """Manually assign admin role to a member"""
        admin_role = discord.utils.get(ctx.guild.roles, name=CONFIG["roles"]["admin"]["name"])
        if not admin_role:
            await ctx.send("❌ Admin role not found!")
            return
        
        if admin_role in member.roles:
            await ctx.send(f"✅ {member.mention} already has admin privileges.")
            return
        
        await member.add_roles(admin_role, reason=f"Admin assigned by {ctx.author}")
        await ctx.send(f"👑 Assigned admin privileges to {member.mention}")
        print(f"👑 {member.name} assigned admin by {ctx.author.name}")

    @commands.command(name='invite_admin')
    @commands.has_permissions(administrator=True)
    async def invite_admin_command(self, ctx, username: str):
        """Manually send a server invite to a potential admin"""
        try:
            # Create invite
            invite = await ctx.channel.create_invite(
                max_age=604800,  # 7 days
                max_uses=1,
                unique=True,
                reason=f"Manual admin invite for {username}"
            )
            
            await ctx.send(f"✅ Created invite for `{username}`: {invite.url}")
            print(f"📋 Manual invite created for {username} by {ctx.author.name}")
            
        except Exception as e:
            await ctx.send(f"❌ Error creating invite: {e}")

    @commands.command(name='pending_invites')
    @commands.has_permissions(administrator=True)
    async def check_pending_invites(self, ctx):
        """Check pending admin invites"""
        try:
            invite_file_path = os.path.join(os.path.dirname(__file__), "pending_invites.json")
            if not os.path.exists(invite_file_path):
                await ctx.send("❌ No pending invites found.")
                return
            
            with open(invite_file_path, 'r') as f:
                pending_invites = json.load(f)
            
            if not pending_invites:
                await ctx.send("❌ No pending invites found.")
                return
            
            embed = discord.Embed(
                title="📧 Pending Admin Invites",
                color=0xFFD700
            )
            
            for invite in pending_invites:
                embed.add_field(
                    name=f"👤 {invite['username']}",
                    value=(
                        f"**Role:** {invite['role'].title()}\n"
                        f"**Status:** {invite['status'].title()}\n"
                        f"**Created:** {invite['created_date'][:10]}\n"
                        f"**Invite:** {invite['invite_url']}"
                    ),
                    inline=True
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error checking pending invites: {e}")

    async def send_admin_invites(self, guild):
        """Send Discord server invite to additional admins via DM"""
        print("Sending server invites to additional admins...")
        
        # Create a permanent invite link
        try:
            # Use the welcome channel for the invite
            welcome_channel = discord.utils.get(guild.channels, name="welcome")
            if not welcome_channel:
                welcome_channel = guild.system_channel or guild.text_channels[0]
            
            invite = await welcome_channel.create_invite(
                max_age=0,  # Never expires
                max_uses=1,  # Single use for security
                unique=True,
                reason="Admin invite for unkai.gaming_62749"
            )
            
            print(f"✅ Created invite link: {invite.url}")
            
            # Send DM to each additional admin
            for admin_config in CONFIG.get("additional_admins", []):
                username = admin_config["username"]
                
                # Try to find the user across all mutual servers
                target_user = None
                for member in self.get_all_members():
                    if member.name.lower() == username.lower():
                        target_user = member
                        break
                
                if target_user:
                    try:
                        embed = discord.Embed(
                            title="🌟 GlowStatus Discord Server Invitation",
                            description=f"You've been invited to join the official **GlowStatus** Discord server as an admin!",
                            color=0x00FF7F
                        )
                        
                        embed.add_field(
                            name="🔗 Server Info",
                            value=(
                                f"**Server:** {guild.name}\n"
                                f"**Members:** {guild.member_count}\n"
                                f"**Your Role:** 🛡️ Admin\n"
                                f"**Invite:** {invite.url}"
                            ),
                            inline=False
                        )
                        
                        embed.add_field(
                            name="📁 What to Expect",
                            value=(
                                "🟢 **Info:** Welcome, rules, announcements\n"
                                "🔧 **Support:** Help users with setup and issues\n"
                                "🔨 **Development:** GitHub updates and tech discussion\n"
                                "☕ **Lounge:** General community chat"
                            ),
                            inline=False
                        )
                        
                        embed.add_field(
                            name="👑 Admin Privileges",
                            value=(
                                "• Full server administration\n"
                                "• Manage channels and roles\n"
                                "• Moderate community discussions\n"
                                "• Access to GitHub webhook notifications"
                            ),
                            inline=False
                        )
                        
                        embed.set_footer(text="This invite expires after one use for security. Welcome to the team!")
                        
                        await target_user.send(embed=embed)
                        print(f"📧 Sent Discord invite to {username}")
                        
                    except discord.Forbidden:
                        print(f"❌ Could not send DM to {username} - they may have DMs disabled")
                        print(f"   Manual invite needed: {invite.url}")
                    except Exception as e:
                        print(f"❌ Error sending invite to {username}: {e}")
                else:
                    print(f"⚠️ User '{username}' not found in any mutual servers")
                    print(f"   They'll need to join manually: {invite.url}")
                    
                    # Save invite info for manual sharing
                    invite_file_path = os.path.join(os.path.dirname(__file__), "pending_invites.json")
                    pending_invites = []
                    
                    # Load existing pending invites
                    if os.path.exists(invite_file_path):
                        try:
                            with open(invite_file_path, 'r') as f:
                                pending_invites = json.load(f)
                        except:
                            pending_invites = []
                    
                    # Add new invite
                    pending_invites.append({
                        "username": username,
                        "invite_url": invite.url,
                        "role": "admin",
                        "created_date": datetime.now().isoformat(),
                        "status": "pending"
                    })
                    
                    # Save updated invites
                    with open(invite_file_path, 'w') as f:
                        json.dump(pending_invites, f, indent=2)
                    
                    print(f"📄 Saved pending invite for {username} to: {invite_file_path}")
            
        except Exception as e:
            print(f"❌ Error creating invite: {e}")

    async def on_raw_reaction_add(self, payload):
        """Handle reaction events (works even if message isn't in cache)"""
        if payload.user_id == self.user.id:  # Ignore bot's own reactions
            return
        
        guild = self.get_guild(payload.guild_id)
        if not guild:
            return
        
        user = guild.get_member(payload.user_id)
        if not user:
            return
        
        # Check if reaction is on welcome message
        welcome_channel = discord.utils.get(guild.channels, name="welcome")
        if welcome_channel and payload.channel_id == welcome_channel.id:
            if str(payload.emoji) == "👋":
                await self.handle_welcome_reaction(user, guild)

    async def handle_welcome_reaction(self, user, guild):
        """Handle when a user reacts with 👋 to the welcome message"""
        try:
            # Get the verified role
            verified_role = discord.utils.get(guild.roles, name=CONFIG["roles"]["verified"]["name"])
            
            if verified_role and verified_role not in user.roles:
                # Add verified role
                await user.add_roles(verified_role, reason="Reacted to welcome message")
                
                # Send welcome DM
                welcome_dm = discord.Embed(
                    title="👋 Welcome to GlowStatus!",
                    description=f"Thanks for joining, {user.mention}! You've been verified.",
                    color=0x00FF7F
                )
                
                welcome_dm.add_field(
                    name="🎯 Get Started",
                    value=(
                        "• Check out #rules for community guidelines\n"
                        "• Visit #setup-help if you need assistance\n"
                        "• Share your setup in #show-your-glow\n"
                        "• Follow #announcements for updates"
                    ),
                    inline=False
                )
                
                welcome_dm.add_field(
                    name="🔗 Useful Links",
                    value=(
                        "📚 [Documentation](https://github.com/Severswoed/GlowStatus/wiki)\n"
                        "🐛 [Report Issues](https://github.com/Severswoed/GlowStatus/issues)\n"
                        "💡 [Feature Requests](https://github.com/Severswoed/GlowStatus/discussions)"
                    ),
                    inline=False
                )
                
                welcome_dm.set_footer(text="Happy to have you in the GlowStatus community!")
                
                try:
                    await user.send(embed=welcome_dm)
                    print(f"✅ Sent welcome DM to {user.name}")
                except discord.Forbidden:
                    print(f"⚠️ Could not send welcome DM to {user.name} - DMs may be disabled")
                
                # Log the verification
                print(f"✅ {user.name} verified via welcome reaction")
                
                # Send confirmation in general channel
                general_channel = discord.utils.get(guild.channels, name="general")
                if general_channel:
                    await general_channel.send(
                        f"👋 Welcome {user.mention}! You've been verified. "
                        f"Feel free to introduce yourself and let us know how you're using GlowStatus!",
                        delete_after=30
                    )
            else:
                print(f"ℹ️ {user.name} already verified, ignoring welcome reaction")
                
        except Exception as e:
            print(f"❌ Error handling welcome reaction from {user.name}: {e}")

    @commands.command(name='reset_webhooks')
    @commands.has_permissions(administrator=True)
    async def reset_webhooks(self, ctx):
        """Delete all existing webhooks and clear webhook data (admin only)"""
        try:
            webhook_file_path = os.path.join(os.path.dirname(__file__), "active_webhooks.json")
            
            # Delete all existing webhooks in the server
            deleted_count = 0
            for channel in ctx.guild.channels:
                if hasattr(channel, 'webhooks'):
                    try:
                        webhooks = await channel.webhooks()
                        for webhook in webhooks:
                            if webhook.name.startswith("GitHub-"):
                                await webhook.delete(reason=f"Webhook reset by {ctx.author}")
                                deleted_count += 1
                                print(f"🗑️ Deleted webhook: {webhook.name} from #{channel.name}")
                    except Exception as e:
                        print(f"⚠️ Could not delete webhooks from #{channel.name}: {e}")
            
            # Clear webhook data file
            if os.path.exists(webhook_file_path):
                os.remove(webhook_file_path)
                print(f"🗑️ Removed webhook data file")
            
            await ctx.send(f"🗑️ Reset complete! Deleted {deleted_count} GitHub webhooks and cleared data.\n"
                          f"Use `{CONFIG['bot']['command_prefix']}remake_webhooks` to recreate them.")
            
        except Exception as e:
            await ctx.send(f"❌ Error resetting webhooks: {e}")

def main():
    """Run the Discord setup bot"""
    bot = GlowStatusSetup()
    
    if not CONFIG["bot_token"]:
        print("Please set DISCORD_BOT_TOKEN environment variable")
        return
    
    print("� IMPORTANT: Discord Bot Hosting Requirements")
    print("=" * 60)
    print("This Discord bot must run 24/7 to work properly!")
    print("Running locally only works while this terminal is open.")
    print("")
    print("For production use, you need persistent hosting:")
    print("• Free: Railway, Render, or Replit")  
    print("• VPS: DigitalOcean ($5/month), Linode, Vultr")
    print("• Home: Raspberry Pi ($50 one-time)")
    print("")
    print("See discord/DEPLOYMENT.md for setup instructions.")
    print("=" * 60)
    print("")
    
    print("�🛡️ Starting GlowStatus Security Bot...")
    print("Features enabled:")
    print("- Auto-moderation (spam, invites, caps)")
    print("- New member screening")
    print("- Quarantine system")
    print("- Channel lockdown commands")
    print("- Security status monitoring")
    print("- Owner privilege assignment")
    print("- Admin invite system")
    print("- GitHub webhook integration")
    print("- Repository monitoring (GlowStatus, GlowStatus-site)")
    
    try:
        bot.run(CONFIG["bot_token"])
    except Exception as e:
        print(f"Error running bot: {e}")

if __name__ == "__main__":
    main()
